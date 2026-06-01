# Plan: Footage Organizer — Flatten Format Folder, Unify ORGANIZED + FOOTAGE_LIBRARY Structure

**Date:** 2026-04-28
**Status:** Draft
**Request:** Refactor so both `02_ORGANIZED` and `06_FOOTAGE_LIBRARY` use `<category>/<date>/clip.mp4`. Drop the format-folder hierarchy level — format becomes pure index metadata.

---

## What This Does

Unifies the folder structure across the two main video locations so Gray browses the same way everywhere — by category first, then by shoot date. Format (long-form vs short-form) survives as a queryable column in the SQLite index but stops being a folder level. Archive becomes a structure-preserving move (same shape both sides).

Why it matters: Gray's mental model for finding b-roll is "go to the category folder, scan recent dates." Right now ORGANIZED forces him to drill in by date first, which is the opposite of how he actually hunts for clips. Aligning the two layouts also makes the archive step trivial — no path remapping needed.

---

## Current State

**Disk layout today:**
- `02_ORGANIZED/<date>/<format>/<category>/clip.mp4` — date first, format second, category third
- `06_FOOTAGE_LIBRARY/<category>/<date>/clip.mp4` — category first, date second
- 7 dated folders in ORGANIZED (2026-04-19, 04-20, 04-21, 04-22, 04-23, 04-24, 04-27) under the old layout, ~84 clips total
- v2 SQLite index at `D:/Sai/.footage-index.sqlite` — 238 real clips (Premiere noise filtered)

**Code state:**
- `organize_file()` and `archive_file()` in `organizer.py` build destination paths
- `_category_from_path()` in `cli_index.py` has separate parsing branches for the two layouts
- `run_archive()` in `main.py` reads cached category to build the destination — would be simpler if category lived in the path
- **Pre-existing bug:** `pull.py` has unresolved merge conflict markers (commit `34cc612` auto-committed a broken state). The file does not import — `python -c "import pull"` raises `SyntaxError`. Tests passed earlier in the session before this commit landed. **This blocks the refactor; must fix first.**

**Things that won't change:**
- 17-category list in `config.py`
- SQLite schema (the `format` column stays)
- Cache key (filename + filesize) — all existing cache entries still hit
- Day-of-shoot folders stay flat (today's date is the editing scratchpad)
- `01_RAW_INCOMING/<date>/` workflow stays as-is (Gray's choice)

---

## What We're Building

### New
- `plans/2026-04-28-footage-organizer-flatten-format-folder.md` — this plan
- `python-scripts/footage-organizer/migrate_to_flat_structure.py` — one-time throwaway migration script that walks the existing 7 dated folders and moves clips from `<date>/short-form/<cat>/clip.mp4` → `<cat>/<date>/clip.mp4`. Includes pre/post file count check and dry-run mode.

### Modified
- `python-scripts/footage-organizer/pull.py` — resolve merge conflict (keep HEAD side: the `linked` counter is the correct logic — it counts only successful placements, not the input row count)
- `python-scripts/footage-organizer/organizer.py` — `organize_file()` destination changes from `<output_dir>/<date>/<format>/<category>/` to `<output_dir>/<category>/<date>/`. Drop `format_type` parameter entirely (or keep it unused for one release if we want a softer rollback path — recommend dropping cleanly since this is internal API)
- `python-scripts/footage-organizer/main.py`:
  - `run_organize()` — call sites of `organize_file()` no longer pass `fmt`
  - `run_organize()` — add today-skip safety: if `date_str` equals today's date, error out unless `--allow-today` flag is passed (preserves the day-of-flat rule in code, not just convention)
  - `run_archive()` — replace cache-based category lookup with path-based lookup (category is now `parent.name`); walk `02_ORGANIZED/*/<date>/` instead of `02_ORGANIZED/<date>/`
  - Add `--allow-today` flag (escape hatch for the today-skip)
  - Update all docstrings + summary printouts that reference `<date>/<format>/<category>/`
- `python-scripts/footage-organizer/cli_index.py` — `_category_from_path()` collapses to one branch since both shapes are identical now: `rel[0] in (FOOTAGE_LIB, ORGANIZED) → rel[1] is category`
- `python-scripts/footage-organizer/tests/test_pull.py` — fixture seed paths reflect the new shape
- `python-scripts/footage-organizer/tests/test_index.py` — same
- `workflows/footage-organizer.md` — Library Structure block at the top (the contract); Step-by-step section; archive flow section
- `python-scripts/footage-organizer/README.md` — same updates as the workflow doc
- `python-scripts/footage-organizer/CLAUDE.md` — v2 Architecture note already says `06_FOOTAGE_LIBRARY/<category>/<date>/`; add a line stating ORGANIZED now matches

### Deleted
- Nothing structural. The old `<date>/<format>/<category>/` subtrees in 19-27 get walked + emptied by the migration script; empty parent folders pruned at the end.

---

## Step-by-Step Tasks

### Step 0: Fix the pre-existing `pull.py` merge conflict

Open `python-scripts/footage-organizer/pull.py`. Two conflict blocks (lines 47-50 and 67-74). Keep the HEAD side both times — the `linked` counter is the correct return value because it only increments for clips that actually got placed (after the `if not src.exists(): continue` check). The other side returned `len(rows)` which would over-count when source files have gone missing.

Final shape:
```python
fallback_copies = 0
linked = 0
for r in rows:
    src = Path(r.path)
    if not src.exists():
        continue
    # ...placement logic...
    linked += 1

return PullResult(folder=out_folder, count=linked, records=rows, fallback_copies=fallback_copies)
```

Verify: `python -c "import pull"` exits 0. Run `pytest tests/` — should still be 7 passing.

### Step 1: Update `organizer.py`

- `organize_file(src_path, output_dir, date_str, category, move=False)` — drop `format_type` parameter. Destination becomes `os.path.join(output_dir, category, date_str)`.
- `archive_file()` is unchanged — it already takes `category` as the relative subpath.

### Step 2: Update `cli_index.py`

`_category_from_path()` — collapse to one branch. Both `FOOTAGE_LIB/<cat>/<date>/clip.mp4` and `ORGANIZED/<cat>/<date>/clip.mp4` have identical shape. New logic:
```python
if len(rel) >= 4 and rel[0] in (FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED):
    return rel[1]
return "misc"
```

### Step 3: Update `main.py`

- Remove `fmt` argument from the `organize_file()` call inside `run_organize()`. The format detection (orientation + override) still runs and gets stored in the index; it just doesn't shape the path.
- Print summary still groups results by format (informational), but the destination print should say `<category>/<date>/` instead of the old shape.
- `run_archive(client, date_str)`:
  - Old: walks `02_ORGANIZED/<date>/` (one folder), reads cached category per clip, archives.
  - New: walks `02_ORGANIZED/<cat>/<date>/` for each `<cat>` that exists in CATEGORIES, moves each clip to `06_FOOTAGE_LIBRARY/<cat>/<date>/`. No cache lookup needed — category is `clip.parent.parent.name`. After move, prune empty `02_ORGANIZED/<cat>/<date>/` and the now-empty `<cat>/` if no other dates remain.
- Add `--allow-today` flag (parse_args). In the dispatch block, after computing `date_str`, compare to `date.today().strftime("%Y-%m-%d")`. If equal and `--allow-today` not set, print a clear error explaining the rule and exit. Skip this check for `--archive` (archiving today is fine — by convention you never archive a day you haven't already categorized).

### Step 4: Update tests

- `tests/test_pull.py`: paths in `_seed()` don't reference real folder structure, just `tmp_path / "src" / "clip_*.mp4"`. No change needed unless any test asserts a specific folder layout — verify with `pytest tests/`.
- `tests/test_index.py`: same — uses `tmp_path` fixtures. Verify.
- If any test does check old layout, update to new shape.

### Step 5: Write the migration script

Create `python-scripts/footage-organizer/migrate_to_flat_structure.py`:

```python
"""
One-time migration: walks 02_ORGANIZED/<date>/<format>/<category>/clip.mp4
and moves each clip to 02_ORGANIZED/<category>/<date>/clip.mp4.
Reversible — only mv operations on the same drive.

Usage:
  python migrate_to_flat_structure.py --client sai --dry-run    # preview
  python migrate_to_flat_structure.py --client sai              # execute
"""
```

Logic:
1. For each date-named folder under `02_ORGANIZED/` (matches `^\d{4}-\d{2}-\d{2}$`):
   - For each format subdir under it (`long-form/`, `short-form/`):
     - For each category subdir:
       - For each clip:
         - Move to `02_ORGANIZED/<category>/<date>/<filename>`
2. Pre-count clips at every old location; post-count at every new location. Abort if mismatch.
3. After moves complete, prune empty old subtrees (recursively delete empty dirs under each `<date>/`).
4. `--dry-run` flag prints planned moves without executing.

### Step 6: Run the migration

1. Verify clean working tree first (`git status` shows no unstaged changes to organizer code besides this work).
2. `python migrate_to_flat_structure.py --client sai --dry-run` — review planned moves.
3. `python migrate_to_flat_structure.py --client sai` — execute. Should report 84 clips moved (the count we categorized this session).
4. Spot-check on disk: `find D:/Sai/02_ORGANIZED -name "*.MP4" | head -20` shows new shape.

### Step 7: Re-index

```bash
python cli_index.py --client sai index
```

Old paths get marked missing and pruned (`remove_missing` step at end of `cmd_index`). New paths get inserted. Total count should remain ~238.

### Step 8: Update docs in the same commit as code

- `workflows/footage-organizer.md` — replace the Library Structure block:
  ```
  02_ORGANIZED/<category>/<date>/    ← AI-sorted, same shape as FOOTAGE_LIBRARY
  06_FOOTAGE_LIBRARY/<category>/<date>/   ← permanent corpus
  ```
  And the Step-by-step section: clips land in `<category>/<date>/`, no format folder mentioned.
- `python-scripts/footage-organizer/README.md` — same updates. Drop the old format-folder mentions.
- `python-scripts/footage-organizer/CLAUDE.md` — under "v2 Architecture", add a sentence: "ORGANIZED uses the same `<category>/<date>/` shape as FOOTAGE_LIBRARY (since 2026-04-28). Format folders no longer exist; format is index-only metadata."

---

## How to Verify It Works

- [ ] `python -c "import pull"` exits 0 (Step 0 fix)
- [ ] `pytest tests/` reports 7 passing
- [ ] Dry-run migration shows the expected ~84 planned moves
- [ ] After migration: file count of MP4s on disk under `02_ORGANIZED/` matches pre-migration count exactly
- [ ] After migration: zero remaining `<date>/short-form/` or `<date>/long-form/` subtrees in ORGANIZED (verify with `find D:/Sai/02_ORGANIZED -type d -name "short-form" -o -name "long-form" | wc -l` → 0)
- [ ] Re-index reports `Indexed 238 clip(s)` (or close — minor differences if anything else changed). Specifically: 0 clips in misc due to path-parsing fallback.
- [ ] `python main.py --client sai --date <today>` exits with the today-skip error (no `--allow-today`)
- [ ] `python main.py --client sai --date <today> --allow-today` proceeds normally
- [ ] Run a real pull: `python cli_index.py --client sai pull --filmed-date 2026-04-21 --category interview-solo` builds a 9-clip folder
- [ ] Run a real archive: `python main.py --client sai --archive 2026-04-23` moves 3 clips from ORGANIZED → FOOTAGE_LIBRARY at `<cat>/2026-04-23/`. Original ORGANIZED 2026-04-23 paths empty.

---

## Notes

**Trade-offs**

- Dropping the format folder removes a cheap visual signal — at a glance, you can no longer tell whether `2026-04-21/` was a long-form day or a short-form day. The index makes this queryable but not browsable. Gray accepted this for the simplicity gain.
- Day-of-flat enforcement is now in code (`--allow-today` escape hatch). Slight friction if Gray genuinely wants to categorize today's footage in a hurry — has to type one extra flag.
- Migration script is throwaway. Will live in the repo for ~1 commit, can be deleted right after the migration run, or kept as a reference for future structural migrations.

**Risks**

- The merge-conflict bug in `pull.py` is real and pre-existing. Pull operations would have crashed on actual use. The Step 0 fix unblocks both the refactor and any future pull commands.
- If the migration script aborts mid-flight, partial state is recoverable (every operation is a single `shutil.move`, so files are either at old path or new path, never neither). Worst case: re-run the script — it picks up wherever it left off because the "old path exists" check decides per file.

**Follow-ups not in this plan**

- Folder-name-based format detection (vlog/long keywords) — the deferred refactor we agreed to handle later
- Eliminating `01_RAW_INCOMING` — Gray decided to keep
- Pull test on real data — step 5 of the parent 7-step plan, runs after this refactor
- 2026-04-27 Premiere project relocation — step 6 of the parent plan

**One thing to flag at /implement time**

The `--archive` change is the most invasive part of this plan. The new logic walks every category subdir for a given date and moves clips, which means a partially-migrated state (some `<date>/<format>/<category>/` and some `<category>/<date>/` for the same date) would archive incorrectly. The migration must complete fully before any archive runs.
