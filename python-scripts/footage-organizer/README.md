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
1. Scans the dated `01_ORGANIZED/{date}/` folder for `.mp4` / `.mov` files
2. Detects format by orientation: horizontal → `long-form`, vertical → `short-form`
3. Extracts 4 frames per video (at 20/40/60/80% through the clip) via ffmpeg
4. Sends all 4 frames to Claude Haiku Vision in one API call
5. Claude returns one category label
6. File is copied (default) or moved into `01_ORGANIZED/{category}/{date}/`
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

## Footage Library Structure (2026-05-01)

When you run `--archive DATE`, clips move from `01_ORGANIZED/<category>/<date>/` into `05_FOOTAGE_LIBRARY/<category>/<W##_MMM-DD-DD>/`. The week label is computed from the date — W01 = ISO week containing 2026-04-15 (Sai project Day 1).

```
05_FOOTAGE_LIBRARY/
  interview-solo/
    W01_Apr-15-19/     ← Project week 1
      C0001.MP4
    W02_Apr-20-26/     ← Project week 2
      C0034.MP4
  insert-hands/
    W01_Apr-15-19/
      C0019.MP4
```

Library is category-first then week-second — sorts perfectly chronologically AND tells you which week of the Sai project at a glance.

### Weekly workflow (now automatic)

`index` and `pull` auto-create the **current** week's folders before they run, so
you never have to remember to scaffold a week by hand. `create-week` stays as a
manual backfill for a past or future week.

```bash
# Backfill a specific (past or future) week
python cli_index.py --client sai create-week --week 2026-04-13
```

Idempotent — safe to run twice. Only weeks that have been touched exist on disk;
future weeks aren't pre-scaffolded.

### Hard rule: no permanent duplication

Every clip exists in exactly ONE permanent location. Duplicates only live temporarily in `08_QUERY_PULLS/<slug>/` during active editing. After the video ships:

```bash
# Interactive — prompts per-folder keep/delete
python cli_index.py --client sai pull-cleanup

# Bulk-delete pulls older than N days (no prompts)
python cli_index.py --client sai pull-cleanup --older-than 30
```

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
1. Dump card → 01_ORGANIZED/<today>/
2. python main.py --client sai          (Vision categorizes + files into FOOTAGE_LIBRARY/)
3. python cli_index.py --client sai index   (refresh the SQLite index)
4. As you edit, pull working sets:
   python cli_index.py --client sai pull --orientation vertical --filmed-date <day>
   python cli_index.py --client sai pull --category interview-solo --filmed-date <day>
   etc.
```

## v3 — Batch shoots by Vid

When a shoot is a batch of shorts (each video is its own set of takes), file it by Vid in one command instead of hand-sorting:

```bash
python cli_index.py --client sai batch --num 2 \
    --from "01_ORGANIZED/2026-06-07" \
    --map "1:C2493-C2495 2:C2496-C2498 3:C2500"
```

What it does, in order:
1. Ensures this week's folders exist (lazy `ensure_week`).
2. Creates `01_ORGANIZED/Batch_02/Vid_01/`, `Vid_02/`, …
3. Moves each mapped clip range into its Vid folder (the 3 hook takes land together).
4. Re-indexes — tagging those clips `batch_num=2, vid_num=1…` in the SQLite index.
5. Reports anything **unmapped** (video left in the source) and any **mapped clip with no file** — nothing is silently dropped.

- `--from` is relative to the library root (or an absolute path).
- `--map` is space-separated `Vid:clips`, where clips is a single id (`C2500`), a range (`C2493-C2495`), or a comma list (`C2493,C2495`).
- Sony sidecars (e.g. `C2493M01.XML`) move with their clip.
- Re-running is safe — clips already in a Vid folder are left as-is (idempotent).
- **No Vision/AI on batch footage** — it's mapped, not classified, so $0 API spend. The `batch_num`/`vid_num` tags are derived from the folder path, so a plain `index` re-run keeps them correct.

## v3 — Stage transitions (promote)

When a video is finished, `promote` moves the whole project to the next stage so you never forget the step:

```bash
# Active project shipped → Delivered
python cli_index.py --client sai promote --item "Batch 2 Vid 1 - 10 Truths About Ads" --to delivered

# Delivered project retired → Archive
python cli_index.py --client sai promote --item "Subway Challenge Day 1" --to archive
```

- `--to delivered` moves from `02_ACTIVE_PROJECTS`; `--to archive` moves from `03_DELIVERED` (override with `--from active|delivered`).
- The item (a file or folder) is found by exact name; its **format bucket is inferred** from where it lives (pass `--format episodes|linkedin|shorts` if it sits outside one).
- Lands in `<stage>/<format>/<current-week>/` by default — `--week YYYY-MM-DD` targets a specific week, `--no-week` places it loose under the format bucket.
- **Never overwrites** (errors if the destination exists) and **never deletes** — it only moves. Ambiguous names (same name in two buckets) abort with a list. These stages aren't indexed, so the SQLite index is untouched.

## --source flag (cleanup mode)

For loose footage already in your library that needs to be classified:

```bash
python main.py --client sai --source "G:/Sai/loose-april-stuff" --date 2026-04-16
```

Defaults to MOVE (clips relocate into `01_ORGANIZED/<category>/<date>/`). Pass `--copy` if you want originals preserved at the source.

## --format and --top-level-only flags

For shoots where orientation no longer signals format (horizontal shorts, etc.) and folders that contain stuff you don't want walked recursively (Premiere project files, existing categorized output):

```bash
# Override format detection — tag the whole batch as short-form
python main.py --client sai --source "D:/Sai/01_ORGANIZED/2026-04-21" --date 2026-04-21 --format short-form --top-level-only
```

- `--format short-form|long-form` skips orientation detection
- `--top-level-only` processes only `.mp4`/`.mov` at the top level of the source folder (no recursion into subdirs)

## Iteration / Eval Loop

Goal: get classification reliable enough that nothing gets manually re-sorted.

**1. Build a labeled test set** — pick ~40 representative clips from a real shoot day. For each, write down the correct category. Save as a CSV with two columns:

```csv
filepath,correct_category
/Volumes/Footage/Sai/01_ORGANIZED/2026-04-17/C0001.MP4,interview-solo
/Volumes/Footage/Sai/01_ORGANIZED/2026-04-17/C0014.MP4,insert-hands
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
