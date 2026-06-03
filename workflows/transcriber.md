# Workflow: Transcriber

**Status:** LIVE on Windows (GPU Whisper). Mac not set up on purpose — see cross-machine note.
**Cost:** Plain transcript = $0 (local Whisper). `--meeting-notes` adds one Haiku call (~$0.01).
**Script:** `python-scripts/transcriber/`

> _Renamed from `content-pipeline` on 2026-06-02 and stripped to transcription-only. The old
> clip-picking / caption-writing / ffmpeg-cut modules were removed — that half was never used._

---

## Objective

Turn audio or video into text. Two modes:

1. **Transcript** (default) — dump a clean markdown transcript to `output/`.
2. **Meeting notes** (`--meeting-notes`) — voice-memo workflow: transcribe → Haiku extracts Summary / Content Ideas / Decisions / Action Items → saves to Obsidian → deletes the original audio.

`--all` batches every audio/video file in a folder.

---

## ⚠️ Before running `--meeting-notes`

Confirm `.env` keys first — **Gray asked for this reminder on 2026-06-02:**
- `ANTHROPIC_API_KEY` — required for `--meeting-notes` (Haiku writes the notes). It can rotate between machines; a stale key fails the run *after* transcription.
- `OPENAI_API_KEY` — only if local Whisper isn't installed (API fallback).

A plain transcript (no `--meeting-notes`) needs **no keys at all.**

---

## How to Run

```bash
cd python-scripts/transcriber

# Plain transcript (no keys needed)
python main.py path/to/video.mp4

# Voice memo → Obsidian notes (needs ANTHROPIC_API_KEY)
python main.py "C:/Users/Gray Davis/My Drive/Voice Memos/2026-04-19 - idea.m4a" --meeting-notes

# Batch all voice memos in a folder
python main.py "C:/Users/Gray Davis/My Drive/Voice Memos" --meeting-notes --all
```

Output paths:
- Transcript → `output/{name}-transcript-{timestamp}.md`
- Meeting notes → `{OBSIDIAN_VOICE_MEMOS}/{YYYY-MM-DD}-{title}.md` (source audio deleted after)

---

## Setup Checklist (Windows — the home for this tool)

- [ ] `pip install openai-whisper` — the transcriber (local, free)
- [ ] CUDA + `pip install torch --index-url https://download.pytorch.org/whl/cu128` — GPU acceleration on the RTX 5070
- [ ] `ANTHROPIC_API_KEY` in `.env` — for `--meeting-notes`
- [ ] `OBSIDIAN_VOICE_MEMOS` in `.env` — Windows vault path (`C:/Users/Gray Davis/My Drive/Obsidian/Graydient Media/Voice Memos`)
- [ ] `OPENAI_API_KEY` in `.env` — optional fallback

---

## Cross-machine note

- **Whisper lives on Windows.** Your GPU makes it fast and ~95% of editing happens there, so we deliberately did **not** install Whisper on the Mac.
- Code syncs through git. The `.env` keys do **not** (they're gitignored) — create `.env` by hand on each machine.
- On the Mac the Obsidian path default already resolves; on Windows you must set `OBSIDIAN_VOICE_MEMOS`.

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| `--meeting-notes` errors "needs ANTHROPIC_API_KEY" | Add the key to `python-scripts/transcriber/.env` and re-run |
| Whisper not installed | `pip install openai-whisper` (or set `OPENAI_API_KEY` to use the API fallback) |
| Obsidian path not found | Make sure Google Drive for Desktop is synced; set `OBSIDIAN_VOICE_MEMOS` for this machine |
| Output not found | Check the `output/` folder inside `python-scripts/transcriber/` |
