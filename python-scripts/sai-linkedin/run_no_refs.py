"""
One-off: run sai-linkedin WITHOUT the reference posts or Sai voice corpus.
Used to compare the with-references caption vs a plain-prompt caption.
Outputs to <folder>/linkedin-no-refs/ to keep both versions side-by-side.
"""

import json
import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from main import SYSTEM_PROMPT_CORE, parse_srt, MODEL

load_dotenv(Path(__file__).parent / ".env")

folder = Path(sys.argv[1])
srt_path = folder / "master.srt"
transcript = parse_srt(srt_path)
print(f"[no-refs] Transcript ({len(transcript)} chars)")

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

print(f"[no-refs] Calling {MODEL} with NO reference blocks...")
resp = client.messages.create(
    model=MODEL,
    max_tokens=2000,
    system=[{"type": "text", "text": SYSTEM_PROMPT_CORE}],
    messages=[{"role": "user", "content": f"Transcript of today's short:\n\n{transcript}\n\nReturn the JSON."}],
)

raw = resp.content[0].text.strip()
raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
data = json.loads(raw)

out_dir = folder / "linkedin-no-refs"
out_dir.mkdir(exist_ok=True)
(out_dir / "caption.txt").write_text(data["caption"], encoding="utf-8")
(out_dir / "theme.txt").write_text(data["theme"], encoding="utf-8")
(out_dir / "key_points.txt").write_text("\n".join(f"- {p}" for p in data["key_points"]), encoding="utf-8")
(out_dir / "visual_ideas.txt").write_text("\n".join(f"- {v}" for v in data["visual_ideas"]), encoding="utf-8")

usage = resp.usage
print(f"[no-refs] Tokens: in={usage.input_tokens} out={usage.output_tokens}")
print(f"[no-refs] Wrote to {out_dir}/")
print(f"\n--- THEME ---\n{data['theme']}\n")
print(f"--- CAPTION ---\n{data['caption']}\n")
print(f"--- VISUAL IDEAS ---")
for v in data["visual_ideas"]:
    print(f"  - {v}")
