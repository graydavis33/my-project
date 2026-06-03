---
name: transcriber
description: Turn audio/video into text with local Whisper. Two modes — a plain markdown transcript, or a voice-memo workflow that extracts Summary / Content Ideas / Decisions / Action Items and saves them to Obsidian. Triggers when Gray says "transcribe this", "transcribe the voice memo", "make meeting notes from this", or drops an audio/video file to convert to text. Renamed from content-pipeline 2026-06-02 (clip-picking removed).
---

# Transcriber

Transcription only. Whisper turns audio/video into text; that's the whole job.

## When to use
- Gray wants the spoken words out of a video or audio file as text
- A Sai/Gray voice memo (`.m4a`) needs to become structured notes in Obsidian

## ⚠️ Before running `--meeting-notes`
Remind Gray to confirm `ANTHROPIC_API_KEY` (and `OPENAI_API_KEY` if local Whisper isn't installed)
are set in `python-scripts/transcriber/.env`. **Gray explicitly asked for this reminder on 2026-06-02.**
A plain transcript (no `--meeting-notes`) needs no keys.

## Run commands
```bash
cd python-scripts/transcriber
python main.py path/to/video.mp4                       # plain transcript (no keys)
python main.py path/to/voice-memo.m4a --meeting-notes  # notes -> Obsidian (needs ANTHROPIC_API_KEY)
python main.py "path/to/folder" --meeting-notes --all  # batch a folder
```

## Cross-machine
- Whisper lives on **Windows** (GPU, where 95% of editing happens). Not installed on Mac on purpose.
- Code syncs via git; `.env` keys do not — set them by hand per machine.

## Cost
- Plain transcript: free (local Whisper).
- `--meeting-notes`: ~$0.01 per memo (Claude Haiku).
