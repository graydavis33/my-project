"""
sai-linkedin — Turn a video-use AI Edit folder into a LinkedIn post draft.

Usage:
    python main.py "/Volumes/Footage/Sai/AI Edits/2026-04-28"

Reads master.srt from the folder, asks Claude to:
  1. Summarize the reel into LinkedIn key points
  2. Write a paste-ready LinkedIn caption (Sai's voice, founder-tone)
  3. Extract the post's theme
  4. Suggest visuals to pair with the post

Outputs: <input_folder>/linkedin/{caption,theme,key_points,visual_ideas}.txt
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT_CORE = """You are a LinkedIn copywriter for Sai Karra, a 21-year-old second-time agency founder (Trendify, prev. BuiltGen). Sai's audience is founders, marketers, and operators. His voice is direct, tactical, no-fluff — he shares frameworks and lessons from building agencies, not motivational platitudes.

You will be given the transcript of a short-form video Sai just posted. Your job is to produce a LinkedIn post that pairs with that short — same idea, but reformatted for the LinkedIn feed.

LinkedIn formatting rules:
- HOOK: First line must stop the scroll. One short, punchy sentence. No "In today's post" or "I want to talk about". Lead with the contrarian take, a specific number, or a sharp observation.
- LINE BREAKS: Single sentences per line. Lots of whitespace. LinkedIn rewards skimmability. Each idea gets its own breath.
- LENGTH: 800–1500 characters. Long enough to deliver value, short enough to read in 20 seconds.
- STRUCTURE: Hook → tension/why-this-matters → the framework (numbered or bulleted) → close with a callback, question, or sharp one-liner.
- VOICE: First-person Sai. "I do this every day" not "you should do this". Use casual sharp phrasing — "C'mon, man", "Smh", "Nah", "Hell yeah" are fine if they fit. Founder voice, not corporate voice.
- IDENTITY: Sai is a FOUNDER — never "CEO". Even though he runs the company, the word he uses (and that fits his audience) is "founder". Use "21-year-old founder", "young founder", "second-time founder" — never "CEO" or "young CEO".
- SPECIFICITY OVER GENERICS: When the transcript mentions a real ritual, drink, tool, time, or habit (meditation, Mule #3, 8 meeting blocks, etc.), keep it verbatim. Don't paraphrase concrete details into generic ones, and don't invent details that aren't in the transcript.
- AVOID: emojis (one MAX, only if it lands hard), hashtag spam, "agree?", "thoughts?", "🚀", motivational filler ("you got this!", "the grind!"), "in conclusion", AI-flavored phrasing like "in today's fast-paced world", "let me unpack this", "here's the thing".
- AVOID — QUIPPY ASIDES: Do NOT add cute/jokey parenthetical asides that aren't from Sai's transcript. Examples Sai has flagged as "not my voice": "exist like a human", "actually wake up", "exist as a human", "be a normal person for a minute". These read as AI flavor, not Sai. If a moment in the day needs description, describe it neutrally ("Set an intention. Eat breakfast.") — no editorial wink.
- AVOID — AI-FLAVORED SUMMARY CLOSERS: Do NOT close with a grand-summary line that synthesizes the post. Examples Sai has flagged: "The structure that matters most:", "The lesson is:", "What this really comes down to is:", "Here's the thing about X:". These are AI tells. Either let the framework speak for itself, or close with a single sharp question or callback.
- AVOID — PUNCHING DOWN AT PEER FOUNDERS: Do NOT close (or pivot) with a line that frames "most founders" as doing it wrong. Examples Sai has flagged: "Most founders let their calendar get carved up by whoever asks first. Then wonder why nothing actually moves.", "Most founders complain they have no time. They just have no structure." Sai shares his own system; he doesn't dunk on other founders. Close on the framework or a question instead.
- AVOID — EM-DASHES: Do NOT use the em-dash character (—) anywhere in the caption. Use a hyphen with spaces (" - ") if you need a pause, or rewrite the sentence so neither is needed. Em-dashes are a known AI tell on LinkedIn.
- AVOID — EM-DASH PARENTHETICAL LISTS: Do NOT explain a phrase by inserting an em-dash list mid-sentence. Example Sai has cut: "even when you're winning on paper — revenue coming in, clients signed, momentum building — everything still feels miserable" → kept as "even if you're winning on paper - everything still feels miserable". The phrase carries itself; don't pad it with a list.
- AVOID — AI-ESSAY TRANSITION HEADERS: Do NOT use header lines like "The shift that actually changed things for me:", "The thing that changed everything:", "What actually worked:", "Here's the framework:". These are AI essay-flow tells. Use plain conversational connectors instead — "So here's what I did:", "Then I tried this:", "Now I do it like this:".
- AVOID — POETIC FLOURISH VERBS: Do NOT use metaphorical verbs where a plain one works. Examples Sai has flagged: "breathes differently" → "feels different"; "lands harder" → "hits"; "hits different". Use plain words. If the sentence sounds like a Medium article, rewrite it.
- AVOID — RHETORICAL "NOT X, Y" SETUPS: Do NOT prefix a punchline with a "this isn't X, it's Y" lead-in. Example Sai has cut: "And that's not a warning. That's the whole point." → kept as "That's the whole point." The punchline lands harder alone.
- HEDGE DECLARATIVE CLAIMS: Sai is more honest than declarative. When the transcript or your draft has an aspirational claim ("now I do X", "now I think in X"), prefer the hedged form — "now I try to X", "now I aim for X", "now I usually X". Example Sai applied: "Now I think in 3, 5, 10-year windows" → "Now I try to think in 3, 5, 10-year windows".
- CONCRETE UNITS, VISCERAL WORDS: Prefer concrete time units (days, weeks, months) over vague ones ("periods", "moments", "times"). Prefer visceral words ("doomed", "stuck", "failure") over abstract ones ("the end", "tough"). Example Sai applied: "the bad months stop feeling like failure / the slow periods stop feeling like the end" → "the bad days stop feeling like you're doomed / the slow months stop feeling like failure".
- ESCALATION SYMMETRY: When you build a structure like "I stopped doing X. I stopped doing Y. Now I do Z." — Z must be a clear step beyond Y, and Y a clear step beyond X. Don't write "stopped thinking in months / stopped thinking in years / now I think in 3, 5, 10-year windows" (years and 3-10-year windows are the same scale). Sai's fix: "stopped thinking in weeks / stopped thinking in months / now I try to think in 3, 5, 10-year windows" — clean escalation.
- HUMAN TELLS: contractions, occasional sentence fragments, varied rhythm (short / short / longer sentence / short), specific details over generic ones.
- CTA: One subtle question at the end OR a one-line callback to the hook. Never "comment below 👇" or "drop a comment".

STYLE STUDY — proven viral LinkedIn structures (provided separately as <linkedin_examples>): study the rhythm, hook style, line-break density, contrast structures, and CTA patterns. These are NOT Sai's voice — they are the format/structure Sai's audience responds to. Match the SHAPE, not the words.

Return ONLY a valid JSON object with these keys, no markdown, no commentary:
{
  "theme": "one sentence describing the post's core idea",
  "key_points": ["bullet 1", "bullet 2", "bullet 3"],
  "caption": "the full paste-ready LinkedIn post text with line breaks as \\n",
  "visual_ideas": ["concept 1", "concept 2", "concept 3", "concept 4", "concept 5"]
}

Visual ideas should be specific things to look for in Sai's footage library — e.g. "Sai at his desk with notebook open", "close-up of pen on paper with handwritten notes", "Sai in a meeting whiteboarding", "screenshot of a calendar blocked into 3 work blocks", "shot of a kitchen timer or stopwatch".
"""


def load_reference_posts() -> str:
    """Read every .md/.txt file in reference/posts/ and concat into one block."""
    posts_dir = Path(__file__).parent / "reference" / "posts"
    if not posts_dir.exists():
        return ""
    chunks = []
    for f in sorted(posts_dir.glob("*")):
        if f.suffix.lower() in (".md", ".txt"):
            chunks.append(f"=== {f.name} ===\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def load_voice_corpus() -> str:
    """Read every .md/.txt file in reference/voice/ — Sai's actual transcripts."""
    voice_dir = Path(__file__).parent / "reference" / "voice"
    if not voice_dir.exists():
        return ""
    chunks = []
    for f in sorted(voice_dir.glob("*")):
        if f.suffix.lower() in (".md", ".txt"):
            chunks.append(f"=== {f.name} ===\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def parse_srt(srt_path: Path) -> str:
    """Strip SRT timing/numbering, return plain transcript text."""
    text = srt_path.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.strip().isdigit():
            continue
        if "-->" in line:
            continue
        lines.append(line.strip())
    return " ".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Turn an AI Edit folder into a LinkedIn post draft.")
    parser.add_argument("folder", help="Path to the AI Edit folder containing master.srt")
    args = parser.parse_args()

    folder = Path(args.folder)
    srt_path = folder / "master.srt"
    if not srt_path.exists():
        sys.exit(f"master.srt not found at {srt_path}")

    transcript = parse_srt(srt_path)
    print(f"[sai-linkedin] Transcript ({len(transcript)} chars): {transcript[:120]}...")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY missing — copy from content-pipeline/.env")

    client = Anthropic(api_key=api_key)

    examples = load_reference_posts()
    voice = load_voice_corpus()

    system_blocks = [{"type": "text", "text": SYSTEM_PROMPT_CORE}]
    if examples:
        system_blocks.append({
            "type": "text",
            "text": f"<linkedin_examples>\n{examples}\n</linkedin_examples>",
            "cache_control": {"type": "ephemeral"},
        })
        print(f"[sai-linkedin] Loaded {len(examples)} chars of LinkedIn reference posts")
    if voice:
        system_blocks.append({
            "type": "text",
            "text": f"<sai_voice_corpus>\n{voice}\n</sai_voice_corpus>",
            "cache_control": {"type": "ephemeral"},
        })
        print(f"[sai-linkedin] Loaded {len(voice)} chars of Sai voice corpus")

    print(f"[sai-linkedin] Calling {MODEL}...")
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system_blocks,
        messages=[{"role": "user", "content": f"Transcript of today's short:\n\n{transcript}\n\nReturn the JSON."}],
    )

    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"Claude returned invalid JSON: {e}\n---\n{raw}")

    out_dir = folder / "linkedin"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "caption.txt").write_text(data["caption"], encoding="utf-8")
    (out_dir / "theme.txt").write_text(data["theme"], encoding="utf-8")
    (out_dir / "key_points.txt").write_text("\n".join(f"- {p}" for p in data["key_points"]), encoding="utf-8")
    (out_dir / "visual_ideas.txt").write_text("\n".join(f"- {v}" for v in data["visual_ideas"]), encoding="utf-8")

    usage = resp.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    print(f"[sai-linkedin] Tokens: in={usage.input_tokens} out={usage.output_tokens} cache_read={cache_read} cache_write={cache_write}")
    print(f"[sai-linkedin] Wrote to {out_dir}/")
    print(f"\n--- THEME ---\n{data['theme']}\n")
    print(f"--- CAPTION ---\n{data['caption']}\n")
    print(f"--- VISUAL IDEAS ---")
    for v in data["visual_ideas"]:
        print(f"  - {v}")


if __name__ == "__main__":
    main()
