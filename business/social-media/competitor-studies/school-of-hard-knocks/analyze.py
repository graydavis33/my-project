"""
School of Hard Knocks reel study pipeline.

Idempotent — re-running skips finished work.

Stages:
  1. Transcribe each reel via OpenAI Whisper API → transcripts/{slug}.json
  2. Extract 4 key frames per reel via ffmpeg → frames/{slug}/{0..3}.jpg
  3. Analyze each frame via Claude Haiku Vision → frames/{slug}/analysis.json
  4. Detect scene-change cuts via ffmpeg → cuts/{slug}.json
  5. Aggregate everything into data.csv
  6. Generate crash-course.md + playbook.md via Claude Sonnet

Run:
    python analyze.py
"""

import os, sys, json, base64, subprocess, csv
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
REELS = ROOT / "reels"
TRANSCRIPTS = ROOT / "transcripts"
FRAMES = ROOT / "frames"
CUTS = ROOT / "cuts"

# Reuse content-pipeline's .env (has both ANTHROPIC + OPENAI keys)
load_dotenv("/Users/graydavis28/Desktop/my-project/python-scripts/content-pipeline/.env")

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

LABELS = {}
with open(ROOT / "labels.csv") as f:
    for row in csv.DictReader(f):
        LABELS[row["reel_id"]] = row


def reel_files():
    """Yield (rank, reel_id, mp4_path) for each downloaded reel, in rank order."""
    for mp4 in sorted(REELS.glob("*.mp4")):
        stem = mp4.stem  # e.g. "01-DKAP1_DS4fA"
        rank, reel_id = stem.split("-", 1)
        yield int(rank), reel_id, mp4


def transcribe_reel(rank, reel_id, mp4):
    out = TRANSCRIPTS / f"{rank:02d}-{reel_id}.json"
    if out.exists():
        return

    # Whisper API has a 25MB file limit — extract audio if reel is bigger.
    audio_path = mp4
    if mp4.stat().st_size / (1024 * 1024) > 25:
        audio_path = mp4.with_suffix(".mp3")
        if not audio_path.exists():
            subprocess.run([
                "ffmpeg", "-y", "-i", str(mp4),
                "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k",
                str(audio_path)
            ], capture_output=True, check=True)

    print(f"  [{rank:02d}] Transcribing {reel_id}...")
    with open(audio_path, "rb") as f:
        result = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )

    out.write_text(json.dumps({
        "duration": result.duration,
        "text": result.text,
        "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in result.segments],
        "words": [{"start": w.start, "end": w.end, "word": w.word} for w in (result.words or [])],
    }, indent=2))


def extract_frames(rank, reel_id, mp4):
    out_dir = FRAMES / f"{rank:02d}-{reel_id}"
    if (out_dir / "3.jpg").exists():
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)
    ]).decode().strip())

    print(f"  [{rank:02d}] Extracting 4 frames from {reel_id}...")
    for i, pct in enumerate([0.05, 0.30, 0.60, 0.95]):
        t = duration * pct
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(t), "-i", str(mp4),
            "-vframes", "1", "-q:v", "2", str(out_dir / f"{i}.jpg")
        ], capture_output=True, check=True)


VISION_PROMPT = """You are analyzing a single frame from a 'School of Hard Knocks' street interview reel for content study.

Output a single JSON object with these exact keys:
- on_screen_text: any visible burned-in text (subtitles, name labels, callouts), exact wording. Empty string if none.
- text_style: font characteristics (color, weight, position) if text is present. Empty if no text.
- shot_type: one of "extreme close-up", "close-up", "medium close-up", "medium", "wide", "extreme wide"
- framing: short description of who/what is in frame and how composed
- subject_appearance: what the human subjects look like (clothing, accessories) in 1 sentence
- setting: where this is filmed (street, lobby, office, gym, etc.) in 2-4 words
- broll: true if this frame shows B-roll/cutaway (no host-and-subject interview frame), false if it's the interview cam
- energy: "low", "medium", or "high" — visible energy/expression of subjects

Return ONLY the JSON, no other text."""


def analyze_frames(rank, reel_id):
    out = FRAMES / f"{rank:02d}-{reel_id}" / "analysis.json"
    if out.exists():
        return
    frame_dir = FRAMES / f"{rank:02d}-{reel_id}"

    print(f"  [{rank:02d}] Analyzing 4 frames of {reel_id}...")
    analyses = []
    for i in range(4):
        with open(frame_dir / f"{i}.jpg", "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()
        msg = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=[{"type": "text", "text": VISION_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": f"Frame {i+1}/4 (at {[5,30,60,95][i]}% of reel)."},
                ],
            }],
        )
        text = msg.content[0].text.strip()
        # Strip markdown code fences if Claude wraps the JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            analyses.append(json.loads(text.strip()))
        except json.JSONDecodeError:
            analyses.append({"raw": text, "parse_error": True})
    out.write_text(json.dumps(analyses, indent=2))


def detect_cuts(rank, reel_id, mp4):
    out = CUTS / f"{rank:02d}-{reel_id}.json"
    if out.exists():
        return

    print(f"  [{rank:02d}] Detecting cuts in {reel_id}...")
    result = subprocess.run([
        "ffmpeg", "-i", str(mp4), "-filter:v",
        "select='gt(scene,0.3)',showinfo", "-f", "null", "-"
    ], capture_output=True, text=True)

    cuts = []
    for line in result.stderr.splitlines():
        if "pts_time:" in line:
            try:
                cuts.append(float(line.split("pts_time:")[1].split()[0]))
            except (ValueError, IndexError):
                pass
    out.write_text(json.dumps({"cut_timestamps": cuts, "cut_count": len(cuts)}, indent=2))


def aggregate():
    rows = []
    for rank, reel_id, mp4 in reel_files():
        slug = f"{rank:02d}-{reel_id}"
        label_row = LABELS.get(reel_id, {})

        transcript = json.loads((TRANSCRIPTS / f"{slug}.json").read_text())
        frame_analyses = json.loads((FRAMES / slug / "analysis.json").read_text())
        cuts = json.loads((CUTS / f"{slug}.json").read_text())

        first_3s_text = " ".join(s["text"] for s in transcript["segments"] if s["start"] < 3)
        last_3s_text = " ".join(
            s["text"] for s in transcript["segments"]
            if s["start"] > transcript["duration"] - 3
        )

        rows.append({
            "rank": rank,
            "label": label_row.get("label", "Random"),
            "url": label_row.get("url", ""),
            "reel_id": reel_id,
            "duration_s": round(transcript["duration"], 1),
            "hook_first_3s": first_3s_text.strip(),
            "outro_last_3s": last_3s_text.strip(),
            "full_transcript": transcript["text"],
            "cut_count": cuts["cut_count"],
            "cuts_per_second": round(cuts["cut_count"] / transcript["duration"], 2) if transcript["duration"] else 0,
            "opening_shot": frame_analyses[0].get("shot_type", ""),
            "opening_text": frame_analyses[0].get("on_screen_text", ""),
            "opening_setting": frame_analyses[0].get("setting", ""),
            "opening_appearance": frame_analyses[0].get("subject_appearance", ""),
            "mid_shot": frame_analyses[2].get("shot_type", ""),
            "mid_text": frame_analyses[2].get("on_screen_text", ""),
            "closing_shot": frame_analyses[3].get("shot_type", ""),
            "closing_text": frame_analyses[3].get("on_screen_text", ""),
            "broll_frames_count": sum(1 for fa in frame_analyses if fa.get("broll")),
            "energy_opening": frame_analyses[0].get("energy", ""),
            "energy_closing": frame_analyses[3].get("energy", ""),
        })

    csv_path = ROOT / "data.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {csv_path}")
    return rows


def write_reports(rows):
    summary_lines = []
    for r in rows:
        summary_lines.append(f"### Rank #{r['rank']} — {r['label']} ({r['url']})")
        summary_lines.append(f"Duration: {r['duration_s']}s | Cuts: {r['cut_count']} ({r['cuts_per_second']}/s) | Setting: {r['opening_setting']} | Energy: {r['energy_opening']}→{r['energy_closing']}")
        summary_lines.append(f"Hook (first 3s): \"{r['hook_first_3s']}\"")
        summary_lines.append(f"Outro (last 3s): \"{r['outro_last_3s']}\"")
        summary_lines.append(f"Shots: {r['opening_shot']} → {r['mid_shot']} → {r['closing_shot']}")
        summary_lines.append(f"On-screen text — open: \"{r['opening_text']}\" | mid: \"{r['mid_text']}\" | close: \"{r['closing_text']}\"")
        summary_lines.append(f"Subject appearance: {r['opening_appearance']}")
        summary_lines.append(f"B-roll frames: {r['broll_frames_count']}/4")
        summary_lines.append(f"Full transcript: {r['full_transcript']}")
        summary_lines.append("")
    summary = "\n".join(summary_lines)

    crash_course_prompt = f"""You are writing a crash-course study guide for Gray, a freelance videographer studying 'School of Hard Knocks' (street interviews of finance/business people on Wall Street). He wants to imitate their reel formula for his client Sai Karra (young CEO content) and his own brand.

You have data from {len(rows)} of their top reels: full transcripts, edit-cut counts, frame analyses (shot types, on-screen text, settings, B-roll usage, energy).

Write crash-course.md with these 16 sections (use exact section numbers and titles):

1. Hook patterns (first 3 seconds) — group hooks into archetypes (e.g. "name a price", "guess my net worth", "you have X, what would you do"). Cite specific reels by rank.
2. Question library — every distinct question grouped by archetype (provocative / finance-specific / lifestyle / gotcha / follow-up). Quote exact wording.
3. Question delivery — phrasing style, pause patterns, host energy
4. Edit timing — avg cuts per reel, distribution, fastest/slowest, what fast vs slow correlates with
5. B-roll / cutaways — frequency by rank, what they cut to
6. On-screen text / captions — patterns in opening_text and closing_text. Are subject names always on screen? When does text appear?
7. Music + sound design — what you can infer from transcripts (any "[music]" mentions, etc.)
8. Camera + framing — shot_type distribution, opening→mid→closing flow patterns
9. Host on-camera presence — what the host says/does (transcript analysis)
10. Setting / locations — opening_setting distribution. Any location pattern?
11. Cold open vs context — when (if ever) is the subject introduced? Through text? Through dialog?
12. Outro / CTA — closing_text + last 3s patterns
13. Long-form → short-form pipeline — clip selection patterns (what makes an out-take into a winning reel?)
14. Posting cadence + caption copy — limited info; note what's available
15. Outlier analysis — what the TOP 5 (ranks 1-5) do that the BOTTOM 10 (ranks 34-43) don't. This is the most important section.
16. Account-level patterns — what we can infer

Be SPECIFIC. Cite reel ranks, exact quotes, exact numbers. Avoid generalizations. Format with clear markdown headers and bullets.

DATA:
{summary}
"""

    print("  Writing crash-course.md (Sonnet)...")
    msg = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": crash_course_prompt}],
    )
    (ROOT / "crash-course.md").write_text(msg.content[0].text)

    crash_course = (ROOT / "crash-course.md").read_text()
    playbook_prompt = f"""You wrote a crash course on School of Hard Knocks' reel formula. Now write playbook.md — an actionable on-set SOP for Gray to apply that formula when filming Sai Karra (his employer, a young CEO).

Sai context: Gray films Sai daily — 1 short/day + 1 LinkedIn/day + 1 long-form/week. Subject is business commentary, CEO life, deal stories, mentorship moments. Goal: reels that grow Sai's audience using the SOHK playbook.

Sections:
1. Pre-shoot checklist (location scouting, framing, equipment, host wardrobe, subject prep)
2. Shot list — exact framings, with reasons cited from the data (e.g. "open on medium close-up because 38/43 of their reels do")
3. Question bank — 30+ questions Gray can ask Sai or his guests, organized by SOHK's question archetypes
4. Hook templates — 5-10 fill-in-the-blank patterns from the top reels (e.g. "How much did you pay for ___?")
5. Edit recipe — exact cut cadence (cuts/sec from data), captions style (font/position rules), B-roll integration rules
6. Outro templates — proven endings (with exact quoted examples from the data)
7. Caption + hashtag template for posting

Be tactical and specific. Format as a checklist Gray can follow on-set with his phone open.

CRASH COURSE:
{crash_course[:8000]}
"""

    print("  Writing playbook.md (Sonnet)...")
    msg = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=12000,
        messages=[{"role": "user", "content": playbook_prompt}],
    )
    (ROOT / "playbook.md").write_text(msg.content[0].text)


def main():
    TRANSCRIPTS.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)
    CUTS.mkdir(exist_ok=True)

    reels = list(reel_files())
    if not reels:
        print("No reels found in reels/ — wait for downloads to finish.")
        sys.exit(1)

    print(f"\n=== Processing {len(reels)} reels ===\n")

    print("[1/5] Transcribing (OpenAI Whisper API)")
    for r in reels:
        transcribe_reel(*r)

    print("\n[2/5] Extracting frames (ffmpeg)")
    for r in reels:
        extract_frames(*r)

    print("\n[3/5] Analyzing frames (Claude Haiku Vision)")
    for r in reels:
        analyze_frames(r[0], r[1])

    print("\n[4/5] Detecting cut points (ffmpeg scene detect)")
    for r in reels:
        detect_cuts(*r)

    print("\n[5/5] Aggregating + writing reports (Claude Sonnet)")
    rows = aggregate()
    write_reports(rows)

    print(f"\nDone. {len(rows)} reels analyzed.")
    print(f"  {ROOT}/crash-course.md")
    print(f"  {ROOT}/playbook.md")
    print(f"  {ROOT}/data.csv")


if __name__ == "__main__":
    main()
