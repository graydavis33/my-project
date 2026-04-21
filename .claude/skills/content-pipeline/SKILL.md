---
name: content-pipeline
description: Video → transcription → Claude picks best clips → captions → optional ffmpeg cuts → full drafts folder (title, caption, X thread, YT description). Triggers when Gray says "process this video", "transcribe and clip", "make a draft folder", or drops a video file path.
---

# Content Pipeline

> ⚠️ SKELETON — fill in when this tool graduates from Assisted → SOP (see `docs/tool-inventory.md`).

## When to use
- Gray hands a raw video + wants edited clips + publish-ready captions
- Voice memo processing (`.m4a` → transcript + meeting notes)
- Long-form → shorts repurposing

## Current stage: Assisted
## Target stage: SOP

## Flow

1. Input: video file path
2. Transcribe (Windows CUDA 12.8 GPU pipeline)
3. Claude picks best clip candidates
4. Generate captions per clip
5. Optional: ffmpeg cut clips into separate files
6. **(Not built yet)** `export_all_formats.py` → drafts folder with title suggestions, TikTok/IG/YT captions, X thread, YT description with timestamps

## Drafts folder convention
`content-pipeline/drafts/YYYY-MM-DD-video-title/`

## Known gaps
- `export_all_formats.py` not built
- No skill.md for voice memo subflow

## Run commands
```
cd python-scripts/content-pipeline && python main.py path/to/video.mp4
```

## Cost
Variable — ~$0.10-0.50 per video depending on length
