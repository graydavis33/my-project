# Footage Organizer

Analyzes raw MP4/MOV files visually using Claude Haiku Vision and organizes them into subfolders by content type.

## Run
```
cd python-scripts/footage-organizer
python main.py /path/to/footage/
python main.py /path/to/footage/ --output ~/Desktop/shoot-march19/
python main.py /path/to/footage/ --move
```

## How It Works
1. Scans input folder for .mp4 / .mov files
2. Extracts 4 frames per video (at 20/40/60/80% through the clip) via ffmpeg
3. Sends all 4 frames to Claude Haiku Vision in one API call
4. Claude returns one category label
5. File is copied (default) or moved into `organized/{category}/`
6. Results cached by filename+filesize — re-runs are free

## Output Categories
- `interviews/` — person speaking to/facing camera
- `broll-people/` — people in candid activity
- `broll-environment/` — landscapes, cityscapes, establishing shots
- `inserts/` — close-ups of objects, food, hands, gear
- `action/` — movement, vehicles, fast-paced sequences
- `graphics-screens/` — screen recordings, monitor footage
- `uncategorized/` — too dark/blurry/ambiguous

## Setup
1. Copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY`
2. Install ffmpeg: https://ffmpeg.org/download.html (make sure it's in PATH)
3. `pip install -r requirements.txt`

## Cost
~$0.003/video using Claude Haiku. 20-clip shoot ≈ $0.06. Re-runs = $0.00 (cache).

## Files
| File | Purpose |
|------|---------|
| main.py | CLI entry + orchestration loop |
| extractor.py | ffprobe duration + ffmpeg frame extraction |
| analyzer.py | Claude Haiku Vision API call |
| organizer.py | Copy/move file into category subfolder |
| cache.py | Permanent file-based cache (.cache.json) |
| config.py | API key, model, categories, constants |
