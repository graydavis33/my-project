# Workflow: Content Pipeline

**Status:** LIVE on Windows (GPU Whisper) + Mac
**Cost:** Local Whisper = $0 | OpenAI Whisper API fallback + ~$0.02–0.05 Claude per video | Voice-memo mode adds one Haiku call
**Script:** `python-scripts/content-pipeline/`

---

## Objective

Multi-purpose media → text + clips tool. Four modes:

1. **Full pipeline** (default) — transcribe → pick best clips → write platform captions → optional ffmpeg cuts
2. **Transcribe-only** — just dump a clean markdown transcript to `output/`
3. **Meeting notes** — voice-memo workflow: transcribe → Haiku extracts Summary / Content Ideas / Decisions / Action Items → saves to Obsidian → deletes original audio
4. **Batch** — process every audio file in a directory with the same mode (currently supports `--meeting-notes --all`)

---

## Inputs Required

- Path to a video or audio file (`.mp4`, `.mov`, `.m4a`)
- Optional: `--context "description"` — Claude uses this to frame clip selection
- Optional: `--no-cut` — skip ffmpeg auto-cutting (still get timestamps)
- Optional: `--transcribe-only` — just produce a transcript, nothing else
- Optional: `--meeting-notes` — voice-memo extraction path (requires `OBSIDIAN_VOICE_MEMOS` in `.env`)
- Optional: `--all` — batch mode; processes every `.m4a` in the passed folder (or `input/` if none passed)

---

## How to Run

```bash
cd python-scripts/content-pipeline

# Full pipeline
python main.py path/to/video.mp4

# Skip ffmpeg cutting
python main.py path/to/video.mp4 --no-cut

# Add context
python main.py path/to/video.mp4 --context "behind the scenes filming a CEO"

# Transcribe only
python main.py path/to/video.mp4 --transcribe-only

# Voice memo → Obsidian notes
python main.py "C:/Users/Gray Davis/My Drive/Voice Memos/2026-04-19 - idea.m4a" --meeting-notes

# Batch all voice memos in a folder
python main.py "C:/Users/Gray Davis/My Drive/Voice Memos" --meeting-notes --all
```

Output paths:
- Full pipeline → `output/{video}-results-{timestamp}.txt`
- Transcribe-only → `output/{video}-transcript-{timestamp}.md`
- Meeting notes → `{OBSIDIAN_VOICE_MEMOS}/{YYYY-MM-DD}-{title}.md` (source audio is deleted after)

---

## What It Does (Full Pipeline)

1. Transcribes via **local Whisper large-v3** (GPU default — ~650 fps on CUDA 12.8; CPU fallback ~60 fps)
2. OpenAI Whisper API is a fallback if local isn't installed
3. Claude Sonnet identifies 3–5 best short-form clip moments with timestamps + reasoning
4. Claude writes platform-specific captions: TikTok, Instagram Reels, YouTube Shorts
5. If ffmpeg is installed: auto-cuts clips at identified timestamps
6. Saves everything to `output/`

## What It Does (Meeting Notes Mode)

1. Transcribes the audio file with local Whisper
2. Haiku extracts structured sections: **Summary · Content Ideas · Decisions & Priorities · Action Items**
3. Writes a note at `{OBSIDIAN_VOICE_MEMOS}/{YYYY-MM-DD}-{title}.md` with backlink to `_Index.md`
4. Filename date prefix (`YYYY-MM-DD - `) is parsed into the note's frontmatter date
5. Deletes the source `.m4a` on success

---

## Setup Checklist

- [ ] `ANTHROPIC_API_KEY` in `.env` — required
- [ ] `pip install openai-whisper` — default transcriber (local, free)
- [ ] CUDA 12.8 + `pip install torch --index-url https://download.pytorch.org/whl/cu128` — required on Blackwell GPUs (RTX 5070) for GPU acceleration
- [ ] `OPENAI_API_KEY` in `.env` — optional fallback if local Whisper not installed
- [ ] ffmpeg installed — optional (auto-cutting). Install: `brew install ffmpeg` (Mac) or download (Windows)
- [ ] `OBSIDIAN_VOICE_MEMOS` in `.env` — required for `--meeting-notes` mode; points at the target Obsidian folder

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| No transcription (no OpenAI key) | Tool will prompt for manual transcript paste — copy/paste from a transcription service |
| ffmpeg not found | Run with `--no-cut` — you get the timestamps and can cut manually in Premiere |
| Claude picks bad clips | Add `--context` with a description of the video — gives Claude better framing |
| Output file not found | Check `output/` folder inside `python-scripts/content-pipeline/` |

---

## Known Constraints

- Longer videos (30+ min) may take a while to transcribe via Whisper
- ffmpeg auto-cut is rough — final polish still done in Premiere/CapCut
- No upload step — captions are generated but posting is manual for now
