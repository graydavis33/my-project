# Plan: Footage Organizer — Week Folders, Library Restructure, AI Edits + Pulls Reorg

**Date:** 2026-05-01
**Status:** Draft
**Request:** Restructure `/Volumes/Footage/Sai/` (`D:/Sai/` on Windows) so the library uses chronologically-sortable weekly folders, pulls + AI edits live in numbered top-level folders, and the workflow enforces "no permanent duplicates."

---

## What This Does

Reshapes the Sai footage tree so it matches Gray's actual mental model:

- `06_FOOTAGE_LIBRARY/<category>/W##_MMM-DD-DD/` — weekly bucketing, numbered from Sai project start (Apr 15, 2026 = W01). Sorts cleanly. Folders auto-created at the start of each week via a new `create-week` command.
- `08_QUERY_PULLS/<slug>/` — temp folder where queries dump duplicated footage. Gets manually deleted via `pull-cleanup` after the edit ships. Lives in the numbered top-level scheme.
- `09_AI_EDITS/<source-clip>/<pipeline>/` — all AI pipeline outputs (LinkedIn, long-form, short-form re-cuts) grouped by source clip. Replaces the unstructured `AI Edits/` folder.

**Why it matters:**

1. **Sort problem** — current library has `Apr 16 – Apr 19/`, `Aug 3 – Aug 9/`, `Aug 10 – Aug 16/` style names that sort alphabetically (Apr, Aug, Dec) and break inside months (`Aug 3` lands after `Aug 24`). Numbered weeks (`W01_Apr-15-19`) sort perfectly and read as "Week 1 of Sai project."
2. **Empty stub problem** — ~600 empty week-range folders pre-scaffolded for the whole year, most won't be used for months. Replacing with on-demand Monday creation keeps the library tidy.
3. **Duplication rule** — Gray's hard rule: only ONE copy of any clip exists permanently. Duplicates only live temporarily in `08_QUERY_PULLS/` during active editing. After publish → folder gets deleted via the new `pull-cleanup` command.
4. **AI edits homeless** — `AI Edits/` floated outside the numbered scheme with no consistent layout. Promoting to `09_AI_EDITS/<source>/<pipeline>/` makes outputs greppable + matches the rest.

---

## Current State

**Disk layout today** (`/Volumes/Footage/Sai/`):
- `00_TEMPLATES/` … `07_ASSETS/` — established numbered structure
- `02_ORGANIZED/<category>/<date>/clip.mp4` — flatten refactor done 2026-05-01, holds 91 clips waiting to be archived
- `06_FOOTAGE_LIBRARY/<category>/` — 17 categories, each with:
  - ~37 empty week-range stub folders (`Apr 16 – Apr 19`, `Aug 3 – Aug 9`, etc.) ← broken sort
  - 1–2 daily folders (`2026-04-16`, `2026-04-17`, `2026-04-18`) holding 104 real MP4s
- `_pulls/` — query result staging, hidden by leading underscore
- `AI Edits/` — flat folder with mixed pipeline outputs (`2026-04-30/long-form/`, `2026-04-23 Hook 1 Do Over V2/linkedin/`)
- `.footage-index.sqlite` — 238-clip SQLite index at library root

**Code state:**
- Archive logic in `main.py:run_archive()` reads `02_ORGANIZED/<cat>/<date>/` and writes to `06_FOOTAGE_LIBRARY/<cat>/<date>/` — needs to be updated to write `<cat>/W##_MMM-DD-DD/` instead.
- No `create-week` command exists yet.
- No `pull-cleanup` command exists yet.
- `cli_index.py` `_category_from_path()` parses both `FOOTAGE_LIB/<cat>/<date>/` and `ORGANIZED/<cat>/<date>/` — needs a small tweak to also accept `<cat>/W##_*/` shape.
- All path operations use `pathlib.Path` — already cross-platform.

**Things that won't change:**
- 17-category list in `config.py`
- SQLite schema (still one row per clip, paths just shift)
- `01_RAW_INCOMING/<date>/` workflow
- The flatten refactor (Steps 0–3 from prior plan, already shipped)
- Migration script for the flatten step (`migrate_to_flat_structure.py`) stays in repo as reference

---

## What We're Building

### New
- `python-scripts/footage-organizer/migrate_library_to_weeks.py` — one-time throwaway migration: deletes ~600 empty week-range stubs, consolidates the 16 daily folders' clips into `W01_Apr-15-19/`. Pre/post MP4 count check + dry-run.
- `python-scripts/footage-organizer/week_utils.py` — small helper module with `week_label_for(date)` returning `W01_Apr-15-19` style strings + `current_week_label()`. Single source of truth for the naming scheme.
- New CLI command: `python cli_index.py --client sai create-week [--week YYYY-MM-DD]` — creates the current week's folder under every category. Idempotent.
- New CLI command: `python cli_index.py --client sai pull-cleanup [--older-than N]` — lists pull folders, prompts per-folder keep/delete. With `--older-than 30` deletes anything 30+ days old non-interactively.
- `plans/2026-05-01-footage-organizer-week-folders-and-restructure.md` — this plan
- `decisions/log.md` — append entries documenting the week-folder scheme + duplication rule

### Modified
- `python-scripts/footage-organizer/config.py`:
  - Add `FOLDER_QUERY_PULLS = "08_QUERY_PULLS"`
  - Add `FOLDER_AI_EDITS = "09_AI_EDITS"`
  - Add `WEEK_PROJECT_START = "2026-04-15"` (Sai project week-1 anchor)
- `python-scripts/footage-organizer/main.py`:
  - `run_archive(client, date_str)` — destination path now uses `week_utils.week_label_for(date_str)` to compute `<cat>/W##_MMM-DD-DD/`. The week folder may already exist (created by `create-week`); falls back to creating if missing.
  - Update summary printout language.
- `python-scripts/footage-organizer/cli_index.py`:
  - `_category_from_path()` — accepts both `<cat>/<YYYY-MM-DD>/` (legacy) and `<cat>/W##_*/` (new). Logic: if `rel[1]` is in CATEGORIES, return it.
  - Add `cmd_create_week()` and `cmd_pull_cleanup()` dispatchers.
  - Subparser entries for `create-week` and `pull-cleanup`.
  - `pull` command: change output dir from `_pulls/` to `08_QUERY_PULLS/`.
- `python-scripts/footage-organizer/tests/test_index.py` — add a fixture covering `<cat>/W##_*/` parsing.
- `python-scripts/footage-organizer/tests/test_pull.py` — output dir asserts `08_QUERY_PULLS/`.
- `workflows/footage-organizer.md` — Library Structure block becomes:
  ```
  06_FOOTAGE_LIBRARY/<category>/W##_MMM-DD-DD/   ← week folders, created Mondays
  08_QUERY_PULLS/<slug>/                          ← temp; deleted after publish
  09_AI_EDITS/<source-clip>/<pipeline>/           ← grouped by source
  ```
  Plus a new "Weekly Workflow" section: every Monday → run `create-week`; after publishing a video → run `pull-cleanup`.
- `python-scripts/footage-organizer/README.md` — same updates.
- `python-scripts/footage-organizer/CLAUDE.md` — add a "Disk structure (2026-05-01)" block reflecting the new scheme.
- `Desktop/my-project/CLAUDE.md` — folder map update if the workspace-root CLAUDE.md references footage-organizer paths.

### Deleted
- ~600 empty week-range stub folders under `06_FOOTAGE_LIBRARY/<category>/` (Apr 16 – Apr 19, Aug 3 – Aug 9, etc.).
- `_pulls/` folder at library root after content moves to `08_QUERY_PULLS/`.
- `AI Edits/` folder at library root after content moves to `09_AI_EDITS/`.
- 6 empty dated folders under `02_ORGANIZED/` (2026-04-19 through 2026-04-24) — leftover from the flatten migration.

### Renamed (rsync-style move)
- `/Volumes/Footage/Sai/_pulls/` → `/Volumes/Footage/Sai/08_QUERY_PULLS/`
- `/Volumes/Footage/Sai/AI Edits/` → `/Volumes/Footage/Sai/09_AI_EDITS/` (and reorganize internal layout per pipeline-output structure)

---

## Step-by-Step Tasks

### Step 1: Write `week_utils.py` (helper module)

Single source of truth for week label generation.

```python
# week_utils.py
from datetime import date, timedelta

PROJECT_START = date(2026, 4, 15)         # Sai project Day 1 (Wed)
PROJECT_W01_MONDAY = date(2026, 4, 13)    # Mon of W01 (ISO week containing Apr 15)
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def week_label_for(d: date) -> str:
    """Return 'W##_MMM-DD-DD' for the ISO week containing d.
    Week 1 = Mon Apr 13, 2026 (the week containing project start Apr 15)."""
    monday = d - timedelta(days=d.weekday())  # Mon of d's week
    sunday = monday + timedelta(days=6)
    week_num = ((monday - PROJECT_W01_MONDAY).days // 7) + 1
    if week_num < 1:
        raise ValueError(f"Date {d} is before project start {PROJECT_START}")
    # Compose 'W01_Apr-15-19' (use Apr 15 not Apr 13 for W01 — partial week)
    start = max(monday, PROJECT_START) if week_num == 1 else monday
    if monday.month == sunday.month:
        return f"W{week_num:02d}_{MONTH_ABBR[start.month-1]}-{start.day}-{sunday.day}"
    else:
        return f"W{week_num:02d}_{MONTH_ABBR[start.month-1]}-{start.day}-{MONTH_ABBR[sunday.month-1]}-{sunday.day}"

def current_week_label() -> str:
    return week_label_for(date.today())
```

Tests in `tests/test_week_utils.py`:
- `week_label_for(date(2026,4,17))` → `'W01_Apr-15-19'`
- `week_label_for(date(2026,4,21))` → `'W02_Apr-20-26'`
- `week_label_for(date(2026,4,29))` → `'W03_Apr-27-May-3'`
- `week_label_for(date(2026,12,28))` → `'W37_Dec-28-Jan-3'` (cross-month edge)

### Step 2: Update `config.py`

Add the three new constants:
```python
FOLDER_QUERY_PULLS = "08_QUERY_PULLS"
FOLDER_AI_EDITS    = "09_AI_EDITS"
WEEK_PROJECT_START = "2026-04-15"  # informational; logic uses week_utils.PROJECT_START
```

### Step 3: Implement `create-week` command in `cli_index.py`

```python
def cmd_create_week(args):
    library = Path(get_library(args.client))
    footage_lib = library / FOLDER_FOOTAGE_LIB
    target_date = date.fromisoformat(args.week) if args.week else date.today()
    label = week_label_for(target_date)
    created = 0
    for category in CATEGORIES:
        path = footage_lib / category / label
        if not path.exists():
            path.mkdir(parents=True)
            created += 1
    print(f"  Created {created} new folder(s) for {label} (skipped {len(CATEGORIES)-created} existing)")
```

Subparser:
```python
p_cw = sub.add_parser("create-week", help="Create this week's folder under every category")
p_cw.add_argument("--week", help="YYYY-MM-DD; defaults to today")
```

### Step 4: Implement `pull-cleanup` command in `cli_index.py`

```python
def cmd_pull_cleanup(args):
    library = Path(get_library(args.client))
    pulls_root = library / FOLDER_QUERY_PULLS
    if not pulls_root.is_dir():
        print(f"  No {FOLDER_QUERY_PULLS}/ folder. Nothing to clean.")
        return
    folders = sorted(p for p in pulls_root.iterdir() if p.is_dir())
    if not folders:
        print(f"  {FOLDER_QUERY_PULLS}/ is empty.")
        return
    cutoff = date.today() - timedelta(days=args.older_than) if args.older_than else None
    for folder in folders:
        age_days = (date.today() - date.fromtimestamp(folder.stat().st_mtime)).days
        clip_count = sum(1 for _ in folder.rglob("*") if _.is_file())
        if cutoff and age_days < args.older_than:
            continue
        prompt = f"  Delete {folder.name}? ({clip_count} files, {age_days}d old) [y/N]: "
        if args.older_than or input(prompt).strip().lower() == "y":
            shutil.rmtree(folder)
            print(f"    deleted {folder.name}")
```

### Step 5: Update `run_archive()` in `main.py`

Two changes:
- Destination path: `06_FOOTAGE_LIBRARY/<cat>/W##_MMM-DD-DD/` (computed from `date_str`)
- Folder may pre-exist (from `create-week`); use `mkdir(exist_ok=True)`

```python
from week_utils import week_label_for
from datetime import date

def run_archive(client, date_str):
    # ... (existing setup)
    week_label = week_label_for(date.fromisoformat(date_str))
    for category, cat_date_dir in date_subtrees:
        videos = find_videos(cat_date_dir)
        for filepath in videos:
            archive_file(filepath, footage_lib, os.path.join(category, week_label), move=True)
            # ...
```

### Step 6: Update `cli_index.py` `_category_from_path()` to accept week shape

```python
def _category_from_path(filepath, library):
    rel = filepath.relative_to(library).parts
    if len(rel) >= 4 and rel[0] in (FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED) and rel[1] in CATEGORIES:
        return rel[1]
    return "misc"
```
The `rel[1] in CATEGORIES` guard is the fix — works for both `<cat>/<date>/` and `<cat>/W##_*/`.

### Step 7: Update `pull` command output dir

In `cli_index.py`, change pull output from `library / "_pulls" / slug` to `library / FOLDER_QUERY_PULLS / slug`.

### Step 8: Update tests

- `tests/test_week_utils.py` — new file, 4–5 cases including cross-month edge.
- `tests/test_index.py` — add a fixture file at `<cat>/W01_Apr-15-19/clip.mp4` and assert `_category_from_path()` returns the category.
- `tests/test_pull.py` — output path asserts `08_QUERY_PULLS/<slug>/`.

Run `pytest tests/`. Should be 9–10 passing.

### Step 9: Migration script — clean stubs + consolidate daily folders

Create `migrate_library_to_weeks.py`:

1. Walk `06_FOOTAGE_LIBRARY/<category>/`.
2. For each subfolder named like `Apr 16 – Apr 19` (regex `^[A-Z][a-z]{2} \d`): if empty, delete it. If has files, abort and report (shouldn't happen — pre-checked).
3. For each subfolder matching `^\d{4}-\d{2}-\d{2}$` (legacy day folder): compute `week_label_for(parsed_date)`, move files to `<category>/<week_label>/<filename>`. Match XML sidecars by stem.
4. Pre/post MP4 count check.
5. `--dry-run` flag.

### Step 10: Run the library migration

```bash
python migrate_library_to_weeks.py --client sai --dry-run    # preview
python migrate_library_to_weeks.py --client sai              # execute
```

Expected: 600 stubs deleted + 104 clips moved into `W01_Apr-15-19/` subfolders.

### Step 11: Rename `_pulls/` → `08_QUERY_PULLS/`

```bash
mv "/Volumes/Footage/Sai/_pulls" "/Volumes/Footage/Sai/08_QUERY_PULLS"
```

(Code already updated in Step 7 to write here.)

### Step 12: Reorganize `AI Edits/` → `09_AI_EDITS/<source>/<pipeline>/`

`AI Edits/` current contents (from earlier inspection):
- `2026-04-23 Hook 1 Do Over V2/linkedin/` → already source-clip-first, just move
- `2026-04-30/long-form/`, `2026-04-30/short-form/`, `2026-04-30/final.mp4`, etc. → these are date-organized, not source-clip-organized

Plan: write a small one-off rename script that:
- Creates `09_AI_EDITS/`
- Moves `AI Edits/<X>/` → `09_AI_EDITS/<X>/` preserving internal structure
- Date-named ones (`2026-04-30/`) get prefixed: `09_AI_EDITS/2026-04-30_dual-cam-long-form/`
- Documents this in a single `09_AI_EDITS/README.md` so future Gray knows the layout

This step is the most ambiguous — re-read with Gray before executing.

### Step 13: Cleanup leftover empty dated folders in ORGANIZED

```bash
rmdir "/Volumes/Footage/Sai/02_ORGANIZED/2026-04-19" \
      "/Volumes/Footage/Sai/02_ORGANIZED/2026-04-20" \
      "/Volumes/Footage/Sai/02_ORGANIZED/2026-04-21" \
      "/Volumes/Footage/Sai/02_ORGANIZED/2026-04-22" \
      "/Volumes/Footage/Sai/02_ORGANIZED/2026-04-23" \
      "/Volumes/Footage/Sai/02_ORGANIZED/2026-04-24"
```
(2026-04-27 has the Premiere project; 2026-04-28 has uncategorized clips. Both stay.)

### Step 14: Relocate 2026-04-27 Premiere project out of ORGANIZED

Move to `03_ACTIVE_PROJECTS/2026-04-27-Schedule/` (Gray to confirm preferred destination).

### Step 15: Run `create-week` for the current week

```bash
python cli_index.py --client sai create-week
```

Today is 2026-05-01 (a Friday) → creates `W03_Apr-27-May-3/` under all 17 categories. Library is now ready for active-week archive operations.

### Step 16: Archive the 91 clips from ORGANIZED → LIBRARY

Per Gray's confirmation, all source videos for these dates are posted. Run:

```bash
python main.py --client sai --archive 2026-04-19   # → W01_Apr-15-19/
python main.py --client sai --archive 2026-04-20   # → W02_Apr-20-26/
python main.py --client sai --archive 2026-04-21   # → W02_Apr-20-26/
python main.py --client sai --archive 2026-04-22   # → W02_Apr-20-26/
python main.py --client sai --archive 2026-04-23   # → W02_Apr-20-26/
python main.py --client sai --archive 2026-04-24   # → W02_Apr-20-26/
python main.py --client sai --archive 2026-04-27   # → W03_Apr-27-May-3/
```

7 commands; each moves clips for one date into the corresponding week folder.

### Step 17: Re-index

```bash
python cli_index.py --client sai index
```

Old paths (legacy day folders, `<cat>/<date>/`) get marked missing. New paths (`<cat>/W##_*/`) get inserted. Total clip count should match the 238 baseline (or 195 after Premiere noise filtered — re-confirm post-migration).

### Step 18: Update docs in same commit as code

- `workflows/footage-organizer.md` — replace Library Structure block, add Weekly Workflow section, add Pull Lifecycle section.
- `python-scripts/footage-organizer/README.md` — new structure block, new commands.
- `python-scripts/footage-organizer/CLAUDE.md` — append a "Disk structure (2026-05-01)" section.
- `decisions/log.md` — two entries:
  1. Library uses numbered week folders (`W##_MMM-DD-DD`) created via `create-week` Mondays.
  2. Hard rule: no permanent file duplication. Pull folders in `08_QUERY_PULLS/` are temp; cleaned via `pull-cleanup` after publish.

---

## How to Verify It Works

- [ ] `pytest tests/` reports 9+ passing (week_utils + existing)
- [ ] `python cli_index.py --client sai create-week` is idempotent — running twice creates 0 new folders the second time
- [ ] `python cli_index.py --client sai pull-cleanup` lists existing pull folders (or reports empty)
- [ ] After Step 10 migration: zero `Apr 16 – Apr 19`-style folders remain; `W01_Apr-15-19/` contains the 104 consolidated clips
- [ ] After Step 11: `_pulls/` folder gone; `08_QUERY_PULLS/` exists at library root
- [ ] After Step 12: `AI Edits/` folder gone; `09_AI_EDITS/` exists with source-clip-first layout
- [ ] After Step 16: 91 clips moved out of `02_ORGANIZED/<cat>/<date>/` into `06_FOOTAGE_LIBRARY/<cat>/W##_*/`. ORGANIZED only has uncategorized 04-28 clips + the (relocated) Premiere project.
- [ ] After Step 17 re-index: SQLite has correct paths. Sample query: `python cli_index.py --client sai pull --category interview-solo --filmed-date 2026-04-21` builds a valid pull folder under `08_QUERY_PULLS/`.
- [ ] Running on Windows: `python cli_index.py --client sai create-week` produces identical folder names to Mac run.

---

## Notes

**Trade-offs**
- Numbered weeks (`W01`...) are tied to 2026. If Sai project continues into 2027, weeks 53+ will exist and sort fine, but the "Apr-15-21" suffix loses its anchor. Acceptable — re-evaluate at year end.
- Empty per-category folders within active weeks (e.g. `crowd-group/W02_Apr-20-26/` is empty because no crowd shots were filmed that week) — Gray accepts this; the visual structure benefit > the empty-folder noise.
- `AI Edits/` reorganization (Step 12) is the most ambiguous — pause before running, confirm internal layout with Gray.

**Cross-platform safety**
- Every disk operation uses `pathlib.Path` + `shutil.move/rmtree`. No backslashes, no drive-letter assumptions.
- `week_utils.py` uses standard `datetime` — identical results on Mac and Windows.
- UTF-8 stdout reconfigured at top of every script entry point.
- New folder names contain no spaces or special chars (`W01_Apr-15-19` — all ASCII, hyphen-separated).

**Risks**
- If `create-week` is run before `migrate_library_to_weeks.py`, you'd end up with duplicate empty folders (`W01_Apr-15-19/` next to old `Apr 16 – Apr 19/`). Migration script handles this — deletes old stubs first.
- Step 12 (AI Edits) touches a folder that contains active project files. Pause mid-flight to confirm renames before executing.

**Follow-ups not in this plan**
- Auto-trigger `create-week` via launchd (Mac) or Task Scheduler (Windows) every Monday at 6am. Defer until Gray has run it manually a few times and the cadence feels right.
- Auto-trigger `pull-cleanup --older-than 30` weekly. Same — manual first.
- Phase 2: Whisper transcripts + semantic search on the index.

**One thing to flag at /implement time**
- Step 12 (AI Edits reorganize) is the most invasive and has the highest "ask Gray first" rating. If we run out of session time, ship Steps 1–11 + 13–18 and leave 12 for a focused next session.
