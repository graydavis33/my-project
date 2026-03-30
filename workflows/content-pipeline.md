# Workflow: Content Pipeline

**Status:** Built on Windows — needs setup on Mac
**Cost:** Whisper transcription (if used) + ~$0.02–0.05 Claude per video
**Script:** `python-scripts/content-pipeline/`

---

## Objective

Take a raw video file → transcribe it → identify the best short-form clip moments → write platform-specific captions → optionally auto-cut the clips with ffmpeg.

---

## Inputs Required

- Path to a video file (`.mp4` or similar)
- Optional: `--context "description"` to help Claude understand the video topic
- Optional: `--no-cut` flag to skip ffmpeg auto-cutting

---

## How to Run

```bash
cd python-scripts/content-pipeline

# Basic run
python main.py path/to/video.mp4

# Skip auto-cut (just get clip list + captions)
python main.py path/to/video.mp4 --no-cut

# Add context about the video
python main.py path/to/video.mp4 --context "behind the scenes filming a CEO"
```

Output: saved to `output/{video}-results-{timestamp}.txt` — cut list + all captions

---

## What It Does (Step by Step)

1. Transcribes video via OpenAI Whisper API (falls back to manual transcript paste if no key)
2. Claude Sonnet identifies 3–5 best short-form clip moments with timestamps + reasoning
3. Claude writes platform-specific captions: TikTok, Instagram Reels, YouTube Shorts
4. If ffmpeg is installed: auto-cuts clips at identified timestamps
5. Saves everything to `output/` folder

---

## Setup Checklist (Mac)

- [ ] `ANTHROPIC_API_KEY` in `.env` — required
- [ ] `OPENAI_API_KEY` in `.env` — optional (enables Whisper auto-transcription)
- [ ] ffmpeg installed — optional (enables auto-cutting). Install: `brew install ffmpeg`

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
