# Content Repurposing Pipeline

## What It Does
- Transcribes video via OpenAI Whisper API (falls back to manual paste if no key)
- Claude identifies 3–5 best short-form clip moments with timestamps + reasoning
- Writes platform-specific captions: TikTok, Instagram Reels, YouTube Shorts
- Optional ffmpeg auto-cut (skips gracefully if not installed)
- Saves cut list + all captions to `output/{video}-results-{timestamp}.txt`

## Key Files
- `main.py` — CLI entry
- `transcriber.py` — Whisper API transcription
- `moment_picker.py` — Claude identifies best clip timestamps
- `caption_writer.py` — Claude generates platform captions
- `video_cutter.py` — ffmpeg auto-cut (optional)
- `config.py` — API keys, settings

## Stack
Python, Claude (claude-sonnet-4-6), OpenAI Whisper API (optional), ffmpeg (optional)

## Run
```bash
cd python-scripts/content-pipeline
python main.py path/to/video.mp4
python main.py path/to/video.mp4 --no-cut
python main.py path/to/video.mp4 --context "description of video"
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (optional — for Whisper auto-transcription)

## Status
Built on Windows. Add `ANTHROPIC_API_KEY` to `.env`. ffmpeg and OpenAI key are optional.
