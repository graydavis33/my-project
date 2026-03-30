# Workflow: Footage Organizer

**Status:** Built on Windows
**Cost:** ~$0.003/video (Claude Haiku Vision). Re-runs = $0 (permanent cache).
**Script:** `python-scripts/footage-organizer/`

---

## Objective

Drop a folder of raw MP4/MOV files → Claude visually analyzes 4 frames per clip → organizes everything into labeled subfolders. Saves hours of manual sorting after a shoot.

---

## How to Run

```bash
cd python-scripts/footage-organizer

python main.py /path/to/footage/                        # Copy files into organized/ subfolders
python main.py /path/to/footage/ --move                 # Move instead of copy
python main.py /path/to/footage/ --output ~/Desktop/shoot-march19/  # Custom output location
```

---

## Output Categories

| Folder | What Goes There |
|--------|----------------|
| `interviews/` | Person speaking to/facing camera |
| `broll-people/` | People in candid activity |
| `broll-environment/` | Landscapes, cityscapes, establishing shots |
| `inserts/` | Close-ups of objects, food, hands, gear |
| `action/` | Movement, vehicles, fast-paced sequences |
| `graphics-screens/` | Screen recordings, monitor footage |
| `uncategorized/` | Too dark, blurry, or ambiguous |

---

## What It Does (Step by Step)

1. Scans input folder for `.mp4` / `.mov` files
2. Extracts 4 frames per video (at 20/40/60/80% through the clip) via ffmpeg
3. Sends all 4 frames to Claude Haiku Vision in one call
4. Returns one category label per clip
5. Copies (or moves) file into `organized/{category}/`
6. Caches result by filename + filesize — same clip never analyzed twice

---

## Setup Checklist

- [ ] `ANTHROPIC_API_KEY` in `.env`
- [ ] ffmpeg installed and in PATH (`brew install ffmpeg` on Mac)
- [ ] `pip install -r requirements.txt`

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| ffmpeg not found | Install ffmpeg: `brew install ffmpeg` (Mac) or download from ffmpeg.org (Windows) |
| Clips landing in `uncategorized/` | Dark or blurry clips — normal. Review and move manually. |
| Re-running after changes | Cache is permanent by filename+filesize. Delete `.cache.json` to re-analyze all clips. |
| API errors | Check `ANTHROPIC_API_KEY` in `.env` |

---

## Cost Estimate

| Shoot Size | Approximate Cost |
|------------|-----------------|
| 20 clips | ~$0.06 |
| 100 clips | ~$0.30 |
| Re-run (any size) | $0.00 |
