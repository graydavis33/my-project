"""find_visuals.py — Vision-scored frame finder for sai-linkedin posts.

For each line in <input_folder>/linkedin/visual_ideas.txt:
  1. Map the idea to candidate footage categories in D:/Sai/.footage-index.sqlite
  2. Sample N frames from the top M candidate clips
  3. Send all frames + the idea description to Claude Haiku 4.5 in one batched call
  4. Pick the highest-scored frame per idea
  5. Extract HQ JPG to <input_folder>/visuals/

Usage:
    python find_visuals.py "D:/Sai/08_AI_EDITS/linkedin/2026-04-16-input-over-output"
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ROOT = Path("D:/Sai")
INDEX = ROOT / ".footage-index.sqlite"
MODEL = "claude-haiku-4-5-20251001"
N_CLIPS_PER_IDEA = 3
N_FRAMES_PER_CLIP = 3
MIN_DATE = "2026-04-15"

# Map each visual-idea (loosely) to a SQL WHERE clause over `category`.
# Order matters — first matching keyword wins.
KEYWORD_TO_WHERE = [
    (r"closeup|close-up|hand|notebook|pen|writing|paper|list|checklist", "category IN ('insert-hands','insert-detail','screens-and-text')"),
    (r"screen|monitor|dashboard|laptop|computer|spreadsheet", "category IN ('screens-and-text','insert-detail')"),
    (r"team|meeting|call|conversation|reviewing|together|with .* member", "category IN ('interview-duo','crowd-group','candid-people')"),
    (r"walk|hallway|street|outside|exterior", "category IN ('walk-and-talk','establishing-exterior')"),
    (r"office|interior|inside|background", "category IN ('establishing-interior','interview-solo')"),
    (r"sai|founder|desk|sitting|talking", "category IN ('interview-solo','reaction-listening')"),
]


def map_idea_to_where(idea: str) -> str:
    """Pick the best WHERE clause for this visual idea based on keywords."""
    s = idea.lower()
    for pattern, where in KEYWORD_TO_WHERE:
        if re.search(pattern, s):
            return where
    return "category IN ('interview-solo','candid-people')"  # fallback


def candidate_clips(con: sqlite3.Connection, idea: str) -> list[tuple[str, float]]:
    where = map_idea_to_where(idea)
    sql = f"""SELECT path, duration_s FROM clips
              WHERE {where} AND filmed_date >= ?
              ORDER BY duration_s DESC LIMIT {N_CLIPS_PER_IDEA}"""
    return [(p, d) for p, d in con.execute(sql, (MIN_DATE,))]


def sample_frames(rel_path: str, duration: float, work_dir: Path, slot: str) -> list[Path]:
    """Extract N evenly-spaced frames from clip into work_dir/<slot>_*.jpg."""
    abs_path = ROOT / rel_path
    if not abs_path.exists():
        return []
    frames = []
    times = [duration * (i + 1) / (N_FRAMES_PER_CLIP + 1) for i in range(N_FRAMES_PER_CLIP)]
    for i, t in enumerate(times):
        out = work_dir / f"{slot}_t{i}.jpg"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t),
                 "-i", str(abs_path), "-frames:v", "1",
                 "-vf", "scale=480:-1",   # downscale for vision API
                 "-q:v", "5", str(out)],
                check=True,
            )
            frames.append(out)
        except subprocess.CalledProcessError:
            continue
    return frames


def b64(p: Path) -> str:
    return base64.standard_b64encode(p.read_bytes()).decode()


def score_frames(client: Anthropic, idea: str, frames: list[tuple[str, Path]]) -> dict[str, int]:
    """frames is list of (label, path). Returns {label: score 0-10}."""
    content = [{"type": "text", "text": (
        f"VISUAL IDEA: \"{idea}\"\n\n"
        f"Below are {len(frames)} candidate frames labeled F0..F{len(frames)-1}. "
        "For each frame, score 0-10 how well it matches the visual idea above. "
        "Score by SUBJECT match first (does the frame depict what the idea describes?), "
        "then by IMAGE QUALITY (in focus, well-composed, usable as a still). "
        "Skip blurry, out-of-focus, motion-blurred, or otherwise unusable frames (score them 0-2). "
        "Return ONLY a JSON object mapping label to integer score, like {\"F0\": 7, \"F1\": 2, ...}. "
        "No prose."
    )}]
    for label, path in frames:
        content.append({"type": "text", "text": f"Frame {label}:"})
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": b64(path),
        }})
    msg = client.messages.create(
        model=MODEL, max_tokens=2000,
        messages=[{"role": "user", "content": content}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def extract_hq_frame(rel_path: str, time_s: float, out_path: Path):
    abs_path = ROOT / rel_path
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(time_s),
         "-i", str(abs_path), "-frames:v", "1", "-q:v", "2", str(out_path)],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    args = ap.parse_args()

    folder = Path(args.folder)
    ideas_path = folder / "linkedin" / "visual_ideas.txt"
    if not ideas_path.exists():
        sys.exit(f"missing {ideas_path}")

    visuals_dir = folder / "visuals"
    visuals_dir.mkdir(exist_ok=True)
    work = visuals_dir / "_candidates"
    work.mkdir(exist_ok=True)

    ideas = [l.lstrip("- ").strip() for l in ideas_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Loaded {len(ideas)} visual ideas")

    api_key = os.environ.get("ANTHROPIC_API_KEY") or _env("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY not set")
    client = Anthropic(api_key=api_key)
    con = sqlite3.connect(str(INDEX))

    results = []
    for idx, idea in enumerate(ideas, 1):
        print(f"\n--- Idea {idx}: {idea[:60]}{'...' if len(idea) > 60 else ''} ---")
        clips = candidate_clips(con, idea)
        if not clips:
            print("  no candidate clips"); continue
        # Sample frames + track which clip/time each came from
        frames = []
        meta = {}
        for c_idx, (rel, dur) in enumerate(clips):
            slot = f"i{idx}_c{c_idx}"
            sampled = sample_frames(rel, dur, work, slot)
            for f_idx, fpath in enumerate(sampled):
                label = f"F{len(frames)}"
                t_s = dur * (f_idx + 1) / (N_FRAMES_PER_CLIP + 1)
                frames.append((label, fpath))
                meta[label] = (rel, t_s, Path(rel).stem)
                print(f"    {label}: {Path(rel).name} @ {t_s:.1f}s")
        if not frames:
            print("  no frames extracted"); continue

        scores = score_frames(client, idea, frames)
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        print("  scores:", ", ".join(f"{l}={s}" for l, s in ranked))
        winner_label, winner_score = ranked[0]
        rel, t_s, stem = meta[winner_label]
        out_name = f"idea{idx}_score{winner_score}_{stem}.jpg"
        out_path = visuals_dir / out_name
        extract_hq_frame(rel, t_s, out_path)
        results.append({"idea": idea, "winner": out_name, "score": winner_score,
                        "source": rel, "time_s": t_s})
        print(f"  WINNER: {out_name} (score {winner_score}/10)")

    summary = visuals_dir / "_summary.json"
    summary.write_text(json.dumps(results, indent=2))
    print(f"\nDone — {len(results)} winners in {visuals_dir}")


def _env(name):
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


if __name__ == "__main__":
    main()
