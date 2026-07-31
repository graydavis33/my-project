---
description: Control what Claude reads aloud (summary / full / off / stop / say)
---

# Voice Control

The user typed `/voice $ARGUMENTS`. Handle the argument as follows.

Mode file: `~/.claude/voice-mode` (contains `summary`, `full`, or `off`).

- **`summary`** (default) — run `echo summary > ~/.claude/voice-mode`.
  Only the 🔊 aimed line gets read aloud. If a response has no 🔊 line,
  the closing paragraph is read instead.
- **`full`** — run `echo full > ~/.claude/voice-mode`. Reads the whole
  response top to bottom (the old behavior).
- **`off`** — run `echo off > ~/.claude/voice-mode` and also
  `pkill -f '^/usr/bin/say'` to stop anything mid-sentence.
- **`on`** — same as `summary`.
- **`stop`** — just `pkill -f '^/usr/bin/say'`. Silences the current
  sentence without changing the mode.
- **`say <text>`** — speak that exact text right now:
  `say -v "Ava (Premium)" -r 150 "<text>"` run in the background.
- **`slower` / `faster`** — edit `RATE` in `~/.claude/hooks/speak-response.py`
  (down or up by 25 wpm) and report the new rate.
- **no argument** — report the current mode (`cat ~/.claude/voice-mode`),
  whether `~/.claude/voice-off` exists, and list these options plainly.

After any change, confirm in one short sentence. Do not re-explain the
whole system unless asked.
