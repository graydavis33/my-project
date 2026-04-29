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

SYSTEM_PROMPT = """You are a LinkedIn copywriter for Sai Karra, a 21-year-old second-time agency founder (Trendify, prev. BuiltGen). Sai's audience is founders, marketers, and operators. His voice is direct, tactical, no-fluff — he shares frameworks and lessons from building agencies, not motivational platitudes.

You will be given the transcript of a short-form video Sai just posted. Your job is to produce a LinkedIn post that pairs with that short — same idea, but reformatted for the LinkedIn feed.

LinkedIn formatting rules:
- HOOK: First line must stop the scroll. One short, punchy sentence. No "In today's post" or "I want to talk about". Lead with the contrarian take or the specific number.
- LINE BREAKS: Single sentences per line. Lots of whitespace. LinkedIn rewards skimmability.
- LENGTH: 800–1300 characters. Long enough to deliver value, short enough to read in 20 seconds.
- STRUCTURE: Hook → tension/why-this-matters → the framework (numbered or bulleted) → close with a question or callback.
- VOICE: First-person Sai. "I do this every day" not "you should do this".
- AVOID: emojis, hashtag spam, "agree?", "thoughts?", "🚀", motivational filler, "in conclusion".
- CTA: One subtle question at the end OR a one-line callback to the hook. Not "comment below 👇".

Return ONLY a valid JSON object with these keys, no markdown, no commentary:
{
  "theme": "one sentence describing the post's core idea",
  "key_points": ["bullet 1", "bullet 2", "bullet 3"],
  "caption": "the full paste-ready LinkedIn post text with line breaks as \\n",
  "visual_ideas": ["concept 1", "concept 2", "concept 3", "concept 4", "concept 5"]
}

Visual ideas should be specific things to look for in Sai's footage library — e.g. "Sai at his desk with notebook open", "close-up of pen on paper with handwritten notes", "Sai in a meeting whiteboarding", "screenshot of a calendar blocked into 3 work blocks", "shot of a kitchen timer or stopwatch".
"""


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

    print(f"[sai-linkedin] Calling {MODEL}...")
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
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
