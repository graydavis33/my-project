#!/usr/bin/env python3
"""
Speak Claude's last response out loud (macOS `say`).

Runs as a Stop hook. Reads the transcript, grabs the final assistant
message, strips out anything that sounds terrible read aloud (code blocks,
file paths, markdown symbols, URLs), then speaks it in the background.

Toggle OFF:  touch ~/.claude/voice-off
Toggle ON :  rm ~/.claude/voice-off
Change voice/speed: edit VOICE and RATE below.
"""

import json
import os
import re
import subprocess
import sys

# "auto" picks the best-quality voice you have installed (Premium > Enhanced >
# basic). Download Premium voices in System Settings > Accessibility >
# Spoken Content > System Voice > Manage Voices — no edit here needed after.
# Set to "auto" to auto-pick the best installed voice instead of a fixed name.
# Note: an uninstalled voice silently falls back to Samantha (no error).
VOICE = "Ava (Premium)"
RATE = 150           # words per minute (175 = normal, 220 = brisk)
MAX_CHARS = 1200     # don't read a novel out loud

# preferred order when VOICE = "auto"; first match wins
VOICE_PREFERENCE = ["Ava", "Zoe", "Evan", "Allison", "Samantha", "Tom", "Nathan"]

HOME = os.path.expanduser("~")
OFF_SWITCH = os.path.join(HOME, ".claude", "voice-off")
VOICE_CACHE = os.path.join(HOME, ".claude", ".voice-cache")


def pick_voice() -> str:
    if VOICE != "auto":
        return VOICE

    # `say -v '?'` takes ~0.3s, so remember the answer between turns
    try:
        with open(VOICE_CACHE) as f:
            cached = f.read().strip()
        if cached:
            return cached
    except OSError:
        pass

    try:
        listing = subprocess.run(
            ["/usr/bin/say", "-v", "?"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return "Samantha"

    installed = []
    for line in listing.splitlines():
        m = re.match(r"^(.+?)\s{2,}([a-z]{2}_[A-Z]{2})", line)
        if m and m.group(2).startswith("en"):
            installed.append(m.group(1).strip())

    best = "Samantha"
    for tier in ("(Premium)", "(Enhanced)", ""):
        ranked = [
            v for base in VOICE_PREFERENCE
            for v in installed
            if v == (f"{base} {tier}".strip())
        ]
        if ranked:
            best = ranked[0]
            break

    try:
        with open(VOICE_CACHE, "w") as f:
            f.write(best)
    except OSError:
        pass
    return best


def clean(text: str) -> str:
    # drop fenced code blocks entirely
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # markdown links -> just the label
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # bare urls
    text = re.sub(r"https?://\S+", "", text)
    # inline code -> plain words
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # file paths
    text = re.sub(r"(~|/)[\w./~-]{6,}", " that file ", text)
    # bullets / headings / emphasis
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_>|#]", " ", text)
    # emoji + symbol junk
    text = re.sub(r"[^\w\s.,!?;:'\"()\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def last_assistant_text(transcript_path: str) -> str:
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    lines = []
    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = entry.get("message", {}).get("content", [])
        if isinstance(content, str):
            return content
        parts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        joined = " ".join(p for p in parts if p.strip())
        if joined.strip():
            return joined
    return ""


def main() -> None:
    if os.path.exists(OFF_SWITCH):
        return

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    text = clean(last_assistant_text(payload.get("transcript_path", "")))
    if not text:
        return

    if len(text) > MAX_CHARS:
        cut = text.rfind(".", 0, MAX_CHARS)
        text = text[: cut + 1 if cut > 200 else MAX_CHARS]

    # stop any speech still playing from the previous turn
    subprocess.run(["pkill", "-f", "^/usr/bin/say"], capture_output=True)
    subprocess.Popen(
        ["/usr/bin/say", "-v", pick_voice(), "-r", str(RATE), text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


if __name__ == "__main__":
    main()
