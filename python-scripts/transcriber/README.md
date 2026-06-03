# Transcriber

Turns audio or video into text using **local Whisper** (free, offline). Two modes:
plain transcript, or voice-memo → structured notes in Obsidian.

> _Renamed from `content-pipeline` on 2026-06-02. The old clip-picking / caption-writing
> half was removed — this tool now does one thing: transcription._

---

## ⚠️ BEFORE YOU RUN `--meeting-notes` — read this

**Update your `.env` keys first:**
- `ANTHROPIC_API_KEY` — required for `--meeting-notes` (Claude Haiku writes the notes)
- `OPENAI_API_KEY` — only needed if local Whisper isn't installed (API fallback)

**Why this reminder exists:** Gray asked Claude on 2026-06-02 to flag this every time, because
the keys can expire/rotate between machines and a stale key makes `--meeting-notes` fail at the
end (after transcription already ran). A plain transcript (no `--meeting-notes`) needs **no keys at all.**

---

## What It Does
- Transcribes any audio/video via **local Whisper** (large-v3), or OpenAI Whisper API as a fallback
- **Default (no flag)** — dumps a clean markdown transcript to `output/`
- `--meeting-notes` — voice-memo workflow: transcribes, extracts Summary / Content Ideas / Decisions & Priorities / Action Items via Claude Haiku, saves to Obsidian, deletes the original audio
- `--all` — batch every audio/video file in a folder

## Key Files
- `main.py` — CLI entry
- `transcriber.py` — Whisper transcription (local default, OpenAI API fallback)
- `config.py` — keys + paths

## Run
```bash
cd python-scripts/transcriber
python main.py path/to/video.mp4                       # plain transcript (no keys needed)
python main.py path/to/voice-memo.m4a --meeting-notes  # notes -> Obsidian (needs ANTHROPIC_API_KEY)
python main.py "path/to/folder" --meeting-notes --all  # batch a whole folder
```

## Env Vars (.env)
- `ANTHROPIC_API_KEY` — required for `--meeting-notes` only
- `OPENAI_API_KEY` — optional (Whisper API fallback if local Whisper isn't installed)
- `OBSIDIAN_VOICE_MEMOS` — where `--meeting-notes` saves. Mac path is the built-in default; **set this on Windows** to the `C:/Users/...` vault path.

## Cross-machine note
- **Whisper lives on Windows** (your GPU makes it fast, and 95% of editing happens there). No need to install Whisper on the Mac.
- Code syncs via git. Keys (`.env`) do **not** — create `.env` by hand on each machine.

## Status
Transcription-only since 2026-06-02. Local Whisper is the default backend.
