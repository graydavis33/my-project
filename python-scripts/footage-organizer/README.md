# Footage Organizer

Analyzes raw MP4/MOV files visually using Claude Haiku Vision and organizes them into subfolders by content type.

## Run
```
cd python-scripts/footage-organizer

# First-time setup for a client library
python main.py --client sai --setup

# Organize today's RAW dump
python main.py --client sai
python main.py --client graydient

# A specific date
python main.py --client sai --date 2026-04-17

# Move instead of copy
python main.py --client sai --move

# Send unused organized clips into the global B-roll library
python main.py --client sai --archive 2026-04-17
```

## How It Works
1. Scans the dated `01_RAW_INCOMING/{date}/` folder for `.mp4` / `.mov` files
2. Detects format by orientation: horizontal → `long-form`, vertical → `short-form`
3. Extracts 4 frames per video (at 20/40/60/80% through the clip) via ffmpeg
4. Sends all 4 frames to Claude Haiku Vision in one API call
5. Claude returns one category label
6. File is copied (default) or moved into `02_ORGANIZED/{date}/{format}/{category}/`
7. Results cached by filename+filesize — re-runs are free

## Output Categories (17)

Mutually exclusive — each clip lands in exactly one. When the model can't choose confidently, it returns `miscellaneous` for manual review.

- **People — on camera:** `interview-solo`, `interview-duo`, `walk-and-talk`
- **People — off camera:** `candid-people`, `reaction-listening`, `crowd-group`
- **Details:** `insert-hands`, `insert-product`, `insert-food-drink`, `insert-detail`
- **Screens:** `screens-and-text`
- **Environments:** `establishing-exterior`, `establishing-interior`, `environment-detail`
- **Movement:** `action-sport-fitness`, `transit-vehicles`
- **Catch-all:** `miscellaneous` (manual review)

## B-Roll Library Structure

When you run `--archive DATE`, clips move from `02_ORGANIZED/{date}/` into `06_BROLL_LIBRARY/{category}/{week-of-date}/`. The week label is the Monday of the ISO week.

```
06_BROLL_LIBRARY/
  interview-solo/
    2026-04-13/     ← week of April 13 (Monday) — clips archived from any day Mon–Sun that week
      C0001.MP4
    2026-04-20/
      C0034.MP4
  insert-hands/
    2026-04-13/
      C0019.MP4
```

This way the global B-roll library stays category-first but you can still see roughly when something was shot.

## Setup
1. Copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY`
2. Set `SAI_LIBRARY_ROOT` and/or `GRAYDIENT_LIBRARY_ROOT` in `.env` to the SSD path
3. Install ffmpeg: https://ffmpeg.org/download.html (must be in PATH)
4. `pip install -r requirements.txt`

## Cost
~$0.003/video using Claude Haiku. 20-clip shoot ≈ $0.06. Re-runs = $0.00 (cache).

## Files
| File | Purpose |
|------|---------|
| main.py | CLI entry + orchestration loop |
| extractor.py | ffprobe duration + ffmpeg frame extraction |
| analyzer.py | Claude Haiku Vision API call + classification prompt |
| organizer.py | Copy/move file into category subfolder |
| cache.py | Permanent file-based cache (.cache.json) |
| config.py | API key, model, categories, constants |
| eval.py | Eval harness — measures accuracy vs a hand-labeled CSV |

## v2 — Index + Pull (Search & Premiere-ready folders)

v2 adds a SQLite index of every clip in your library + a `pull` command that builds Premiere-ready folders via hardlinks. Folders stay the source of truth; the index makes them queryable.

```bash
# Refresh the index (run after every organize)
python cli_index.py --client sai index

# Pull all vertical clips from April 16, 2026
python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16

# Pull every interview-solo clip from the past week
python cli_index.py --client sai pull --category interview-solo --filmed-after 2026-04-20
```

### Daily Sai loop

```
1. Dump card → 01_RAW_INCOMING/<today>/
2. python main.py --client sai          (Vision categorizes + files into FOOTAGE_LIBRARY/)
3. python cli_index.py --client sai index   (refresh the SQLite index)
4. As you edit, pull working sets:
   python cli_index.py --client sai pull --orientation vertical --filmed-date <day>
   python cli_index.py --client sai pull --category interview-solo --filmed-date <day>
   etc.
```

## --source flag (cleanup mode)

For loose footage already in your library that needs to be classified:

```bash
python main.py --client sai --source "G:/Sai/loose-april-stuff" --date 2026-04-16
```

Defaults to MOVE (clips relocate into `02_ORGANIZED/<date>/<format>/<category>/`). Pass `--copy` if you want originals preserved at the source.

## --format and --top-level-only flags

For shoots where orientation no longer signals format (horizontal shorts, etc.) and folders that contain stuff you don't want walked recursively (Premiere project files, existing categorized output):

```bash
# Override format detection — tag the whole batch as short-form
python main.py --client sai --source "D:/Sai/02_ORGANIZED/2026-04-21" --date 2026-04-21 --format short-form --top-level-only
```

- `--format short-form|long-form` skips orientation detection
- `--top-level-only` processes only `.mp4`/`.mov` at the top level of the source folder (no recursion into subdirs)

## Iteration / Eval Loop

Goal: get classification reliable enough that nothing gets manually re-sorted.

**1. Build a labeled test set** — pick ~40 representative clips from a real shoot day. For each, write down the correct category. Save as a CSV with two columns:

```csv
filepath,correct_category
/Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0001.MP4,interview-solo
/Volumes/Footage/Sai/01_RAW_INCOMING/2026-04-17/C0014.MP4,insert-hands
```

Use [test-set-template.csv](test-set-template.csv) as a starting point. Save your real test set as `test-set.csv` (gitignored — paths are local).

**2. Run the eval**

```bash
python eval.py test-set.csv --label "v1-baseline"
```

Output: overall accuracy, per-category accuracy, confusion matrix, full miss list. Saved to `eval_runs/`.

**3. Iterate the prompt** — open [analyzer.py](analyzer.py), tighten the definitions of the categories that got confused, re-run with a new `--label`. Compare logs in `eval_runs/`.

**4. Stop when you're happy** — accuracy plateau + no surprising misses = ship it.

The cache is bypassed during eval, so prompt edits actually re-run on every clip.
