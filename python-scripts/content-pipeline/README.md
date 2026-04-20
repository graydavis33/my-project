# Content Repurposing Pipeline

## What It Does
- Transcribes video/audio via local Whisper (large-v3) or OpenAI Whisper API
- Claude identifies 3–5 best short-form clip moments with timestamps + reasoning
- Writes platform-specific captions: TikTok, Instagram Reels, YouTube Shorts
- Optional ffmpeg auto-cut (skips gracefully if not installed)
- `--transcribe-only` — dumps a clean markdown transcript to `output/`
- `--meeting-notes` — voice-memo workflow: transcribes, extracts Summary / Content Ideas / Decisions & Priorities / Action Items via Claude Haiku, saves to Obsidian, deletes original audio

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
python main.py path/to/video.mp4 --transcribe-only
python main.py path/to/voice-memo.m4a --meeting-notes
```

## Env Vars (.env)
- `ANTHROPIC_API_KEY` (required)
- `OPENAI_API_KEY` (optional — for Whisper API fallback if local Whisper isn't installed)
- `OBSIDIAN_VOICE_MEMOS` (override for `--meeting-notes` output path — required on Windows)

## Status
Built on Windows + Mac. ffmpeg and OpenAI key are optional. Local Whisper (`pip install openai-whisper`) is the default transcription backend.
