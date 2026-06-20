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
1. Scans the dated `01_ORGANIZED/_INBOX/{date}/` drop folder for `.mp4` / `.mov` files
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

Every clip exists in exactly ONE permanent location. Duplicates only live temporarily in `07_QUERY_PULLS/<slug>/` during active editing. After the video ships:

```bash
# Interactive — prompts per-folder keep/delete
python cli_index.py --client sai pull-cleanup

# Bulk-delete pulls older than N days (no prompts)
python cli_index.py --client sai pull-cleanup --older-than 30
```

### Drafts review folder + auto-clean

`03_DELIVERED/drafts/` is a staging area for non-final versions that need a review pass (by Gray, Cy, or anyone) before they're discarded. It holds **neither originals nor finals** — only disposable draft exports — so it self-cleans on the same 7-day idle rule as query pulls:

```bash
# Interactive — prompts per item
python cli_index.py --client sai drafts-cleanup

# Auto-delete drafts untouched N+ days (no prompts)
python cli_index.py --client sai drafts-cleanup --older-than 7
```

**Hard protection:** `drafts-cleanup` **never deletes project files** (`.prproj`, `.aep`/`.aepx`, `.psd`/`.psb`, `.ai`, `.drp`, ...). A loose project file is kept; a subfolder containing one anywhere is skipped whole. Handles loose files and subfolders (the pull sweep only does folders). Dotfiles (`.DS_Store`, `._*`) are ignored.

Both sweeps (query-pulls + drafts) run together daily via one scheduled job — `sweep_query_pulls.bat` (Windows Task Scheduler) / `sweep_query_pulls.sh` (Mac launchd, `com.graydient.footage-query-sweep.plist`). To change the window, edit the `--older-than` value in **both** wrapper scripts.

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
1. Dump card → 01_ORGANIZED/_INBOX/<today>/
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
- The item (a file or folder) is found by exact name; its **format bucket is inferred** from where it lives (pass `--format longform|linkedin|shorts` if it sits outside one).
- Lands in `<stage>/<format>/<current-week>/` by default — `--week YYYY-MM-DD` targets a specific week, `--no-week` places it loose under the format bucket.
- **Never overwrites** (errors if the destination exists) and **never deletes** — it only moves. Ambiguous names (same name in two buckets) abort with a list. These stages aren't indexed, so the SQLite index is untouched.

## v3.1 — Post-delivery cleanup (ship)

When a video is finished and dropped into `03_DELIVERED`, `ship` does the after-the-fact cleanup in one reviewed step — **it shows you the plan and moves nothing until you confirm**:

```bash
python cli_index.py --client sai ship --video "Batch 2 Vid 1 - 10 Truths About Ads"
```

It plans two moves:
1. The matching **edit project** in `02_ACTIVE_PROJECTS` → `04_ARCHIVE/<format>/<week>/`.
2. The video's **raw footage** in `01_ORGANIZED` → its permanent home, then re-indexes. The destination depends on the footage type:
   - **Batch interview originals** (`Batch_NN/Vid_MM`, auto-detected from the video name) → `05_FOOTAGE_LIBRARY/_BATCHES/Batch_NN/Vid_MM/` — their own filing system, by batch/vid, **no week folder**, and **kept out of the b-roll search index** (the `_` prefix). A finished batch's source takes won't clutter footage searches.
   - **Loose b-roll shoots** (passed with `--footage`) → `05_FOOTAGE_LIBRARY/<category>/<week>/` — the normal category/week b-roll scheme.

- It finds the project by name; footage is located by parsing `Batch N Vid M` from the video name, or you pass `--footage <folder>`.
- Overrides: `--project "exact name"`, `--footage <path>`, `--category <library subfolder>`, `--format`, `--week`, `--no-week`, `--yes` (skip the prompt).
- **Safe:** plan-first, pure moves, never overwrites; if it can't find the project or footage it **warns and skips that half** rather than guessing.
- The `_ship_plan` / `_execute_ship` split lets a folder-watcher reuse the same engine headless — the planned "drop a file → auto-plan → approve" trigger.

## Order of operations — a batch video, start to finish

Where the **original** A-cam/B-cam files live at each step. The originals move exactly **once** (at ship), and the AI editor never touches them — it only reads them and writes new files to `08_AI_EDITS/`.

| Step | Command | Originals live in |
|---|---|---|
| 1. Offload the card | drop files | `01_ORGANIZED/_INBOX/<date>/` |
| 2. File the batch | `batch --num N --from … --map …` | `01_ORGANIZED/Batch_NN/Vid_MM/` (inbox auto-clears) |
| 3. AI edit | your AI editor | **stay put**; new clips → `08_AI_EDITS/shorts/<source>/` |
| 4. Edit + export | Premiere → `03_DELIVERED` | still in `Batch_NN/Vid_MM/` |
| 5. Ship / cleanup | `ship --video "…Batch N Vid M…"` | → `05_FOOTAGE_LIBRARY/_BATCHES/Batch_NN/Vid_MM/` (permanent) |

**AI edits are filed by content format** — `08_AI_EDITS/<format>/<source>/`: batch/short-form edits go under `shorts/`, long-form/episode edits under `longform/`. So a batch video's edited clips land in `08_AI_EDITS/shorts/<source>/` (step 3), and a long-form edit lands in `08_AI_EDITS/longform/<source>/`.

Index lifecycle: batch originals **are** searchable (tagged `batch_num`/`vid_num`) while in `01_ORGANIZED` during production, then **drop out of the search index** once `ship` files them into `_BATCHES` — by design, so finished source takes don't clutter b-roll searches.

## v3.2 — Auto-watch delivered → Slack approval (watch_delivered.py)

A background watcher that turns the `ship` engine into the "just drop a file" flow:

```bash
.venv/bin/python watch_delivered.py --client sai
```

When you export/drop a video into `03_DELIVERED`, it:
1. notices the new file and **waits until it stops growing** (export finished),
2. builds the `ship` plan,
3. **posts it to your Slack** — you react ✅ to approve or ❌ to skip,
4. on ✅ it moves the files + re-indexes and reports back in Slack.

**One-time setup:** add `SLACK_BOT_TOKEN` + `SLACK_USER_ID` to `.env` (same values your other tools use). The bot needs the `reactions:read` scope so it can see your ✅. Test the link first:

```bash
.venv/bin/python watch_delivered.py --client sai --self-test   # posts a test msg; react ✅
```

- **Baselines** the existing delivered files on first run, so it only reacts to NEW exports.
- Handled set is persisted in `.ship-watch-state.json` at the library root.
- One watcher per machine (one-scheduler rule); the footage drive is local so it runs on the Mac, not the VPS. Run it in the foreground while testing; daemonize (launchd) only after a clean test.

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
