# Screen Recording Analyzer

Turn a screen recording (someone walking through a workflow) into an analysis bundle an AI agent can read.

## What it does
1. Extracts visual keyframes with ffmpeg (scene-change detection by default, fixed interval as an option)
2. Transcribes the audio with local Whisper (`large-v3`)
3. Writes a `manifest.json` tying every frame to its timestamp in the video

## Output folder
```
output/{video-name}-{YYYYMMDD-HHMMSS}/
  frames/
    frame_00001.jpg
    frame_00002.jpg
    ...
  transcript.md     # timestamped transcript
  manifest.json     # frames + timestamps + duration + video path
```

## Requirements
- `ffmpeg` and `ffprobe` on PATH
- `pip install openai-whisper` (optional — skip with `--no-transcript`)

## Run
```bash
cd python-scripts/screen-recording-analyzer
python main.py "C:/path/to/screen-recording.mp4"
python main.py video.mp4 --interval 5
python main.py video.mp4 --no-transcript
python main.py video.mp4 --out custom/folder
```

## How an AI agent uses the output
See `workflows/screen-recording-to-sop.md`. In short: read every frame as an image + read transcript.md, then produce a structured SOP doc that downstream automation can execute.
