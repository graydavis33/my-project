# Footage Organizer — Working Notes

This tool is in active iteration. The reliability bar: Gray never has to manually re-sort a clip.

## Current state (2026-04-19)
- Format detection: orientation only (horizontal = long-form, vertical = short-form). 4K/1080p doesn't matter.
- 17 mutually-exclusive categories — see README.
- `misc` is the "I'm not sure" bucket — model uses it whenever two categories could fit. Gray reviews those manually.
- Eval harness in `eval.py` measures accuracy against a hand-labeled CSV. Logs go to `eval_runs/`.
- B-Roll Library archive (`--archive DATE`) drops clips into `06_BROLL_LIBRARY/{category}/{week-of-date}/`. Week = Monday of that ISO week, format `YYYY-MM-DD`.

## When asked to "improve the organizer"
1. Run the latest eval first — never tune blind.
2. Look at the confusion matrix. Find the worst-confused pair.
3. Tighten the prompt definitions for that pair specifically. Don't mass-rewrite.
4. Re-run with a new `--label`. Compare against the previous run.
5. Commit prompt changes incrementally — one tightening per commit.

## When asked to "add a category"
- Adding a category is a last resort. First check whether the missed clips fit `miscellaneous` and just need manual review.
- If you do add one: update `CATEGORIES` in `config.py`, add a strict definition with a primary visual question to the prompt in `analyzer.py`, re-label any test-set clips that are now better described by the new category, re-run the eval.

## Don't
- Don't restore the old 4K-based format detection.
- Don't add a `voiceover` category — Gray explicitly rejected it.
- Don't let the model invent categories or land files in unknown folders. The CATEGORIES list is the contract.

## v2 Architecture (2026-04-27)

**Folders are primary classification:**
> The existing 8-folder library (00_TEMPLATES through 07_ASSETS) is unchanged. Vision-classified clips land in `06_FOOTAGE_LIBRARY/<category>/<date>/`. Folders are how Premiere browses, how Gray browses manually, and how categories are defined. The index does NOT replace folders — it sits beside them.

**SQLite index = orthogonal metadata:**
> `.footage-index.sqlite` lives at the library root. One row per clip with: `path, category, format (vertical/horizontal), filmed_date, upload_date, duration_s, width, height, codec, sha1`. Filmed date comes from camera metadata (ffprobe `creation_time`), falling back to file mtime. Built/refreshed via `python cli_index.py --client sai index`.

**Pull builds Premiere-ready folders via hardlinks (NTFS) or copies (exFAT):**
> `python cli_index.py --client sai pull --orientation vertical --filmed-date 2026-04-16` filters the index → hardlinks matching files into `_pulls/<slug>/`. Hardlinks on NTFS = zero extra disk. Falls back to copy when `os.link` raises `OSError`, which happens on cross-drive AND on exFAT-formatted drives (Windows error 1 "Incorrect function"). **Gray's D:/Sai is exFAT, so pulls always copy** — clear `_pulls/` after each edit to reclaim disk. Files are never moved or deleted by `pull`. `result.fallback_copies` reports the count.

> **One clip → one category.** Vision-classifier output is single-label (unchanged from v1). Hardlinks only appear when `pull` builds an output folder.

## Disk Structure (2026-05-01, renumbered later same day — RAW_INCOMING dropped; weekly scheme extended to project folders)

**Library root (`/Volumes/Footage/Sai/` on Mac, `D:/Sai/` on Windows):**
```
00_TEMPLATES/                                            project templates, LUTs, title cards
01_ORGANIZED/<date>/                                     drop loose footage here for the day's shoot
01_ORGANIZED/<category>/<date>/                          AI-categorized output (post-organize)
02_ACTIVE_PROJECTS/<format>/W##_MMM-DD-DD/               active editing projects, weekly
03_DELIVERED/<format>/W##_MMM-DD-DD/                     finished published exports, weekly
04_ARCHIVE/<format>/W##_MMM-DD-DD/                       retired projects, weekly
05_FOOTAGE_LIBRARY/<category>/W##_MMM-DD-DD/             permanent reusable footage, weekly
06_ASSETS/                                               brand assets, fonts, music, SFX
07_QUERY_PULLS/<slug>/                                   temp query results — deleted after publish
08_AI_EDITS/<pipeline>/<source>/                         AI pipeline outputs grouped by pipeline
.footage-index.sqlite                                    SQLite index of all clips
```

**Format buckets** (used in 02/03/04): `episodes/`, `shorts/`, `linkedin/`. Same scheme across all three project folders for symmetry.

**Legacy capitalized folders** (`Longform/`, `Shortform/`, `Paid Ads/` in archive; `Onboarding/` in delivered) are **left alone** — they pre-date the weekly scheme and contain mixed content.

`RAW_INCOMING` was eliminated 2026-05-01: Gray drops loose footage directly into `01_ORGANIZED/<date>/` instead. Running the organizer categorizes those loose files in place into `01_ORGANIZED/<category>/<date>/`.

**`ensure_week` scaffolds across all four W##-bucketed locations** (FOOTAGE_LIBRARY × 17 categories + ACTIVE/DELIVERED/ARCHIVE × 3 formats = 26 folders per week). As of v3 Phase 1 (2026-06-10), `index` and `pull` auto-call `ensure_week(today)` first, so the current week is created automatically — no manual Monday step. `create-week` remains for backfilling a specific past/future week. (`ensure_week` is the shared helper in `cli_index.py`; `create-week` and the lazy auto-call both route through it.)

**v3 Phase 2 — freeform folders (2026-06-15):**
- `_category_from_path` now treats **ANY folder name** under `05_FOOTAGE_LIBRARY/<name>/...` or `01_ORGANIZED/<name>/...` as the category — not just the fixed 17. Gray's own folders index + pull correctly. The AI Vision classifier stays paused; folders are hand-made.
- `ensure_week` now **discovers freeform folders on disk** (top-level dirs in `05_FOOTAGE_LIBRARY`, skipping `_`-prefixed helpers like `_TO_SORT`) and creates the weekly subfolder in each, in addition to the 17 seeded standard categories.
- `_TO_SORT/` is a holding area inside the library for un-categorized shoots Gray will sort by hand; underscore prefix keeps it out of week-scaffolding.

**v3 Phase 3 — batch command (2026-06-15):**
- `batch --num N --from <folder> --map "1:Cxxxx-Cyyyy …"` files a batch shoot into `01_ORGANIZED/Batch_NN/Vid_MM/` then re-indexes. The pure move logic (`_file_batch`) is split from the re-index so it's unit-testable without ffprobe.
- `batch_num` / `vid_num` are NEW index columns, **derived from the folder path** by `_batch_vid_from_path` (adjacent `Batch_NN` + `Vid_MM` parts) — same folders-are-truth pattern as `_category_from_path`, so a plain `index` re-derives them.
- Schema change is **non-destructive**: `index._migrate` runs `ALTER TABLE ADD COLUMN` for the two columns if missing (NOT a rebuild), so the live 800+-clip DB keeps every row. `idx_batch` is created inside `_migrate` (after the columns exist), never in `_SCHEMA` — putting it in `_SCHEMA` crashed migrating an old DB (`CREATE INDEX` ran before `ALTER`).
- `--map` parsing: `_parse_map` → `_expand_clip_segment` (ranges preserve zero-pad width). `_matching_files` moves Sony sidecars (`C2493M01.XML`) with their clip; a non-digit guard stops `C249` matching `C2493`.
- Reports unmapped source clips + mapped-but-missing clips; idempotent re-run; no Vision ($0).

**v3 Phase 4 — promote / stage transitions (2026-06-15, v3 COMPLETE):**
- `promote --item NAME --to {delivered|archive}` moves a finished project to the next stage. `--from` defaults via `_DEFAULT_FROM` (active→delivered, delivered→archive). Format inferred by `_infer_format` from the item's location (or `--format`); lands in `<stage>/<format>/<week?>/` (current week default; `--week`/`--no-week`).
- `_find_stage_item` is an exact-name search that PRUNES into a matched dir (returns the project folder whole, not its children); >1 match aborts with a list.
- Pure file move (`_promote_item`): never copies/deletes/overwrites (dest-exists aborts). Stages 02/03/04 are NOT in `INDEX_SCAN_ROOTS`, so there's no index/ffprobe involvement — that's why it's pure file ops.

**v3.1 — ship (post-delivery cleanup, 2026-06-15):**
- `ship --video NAME` chains the two cleanup moves after a video is delivered: edit project (02 → 04_ARCHIVE) + raw footage (01 → 05_FOOTAGE_LIBRARY/<video>/<week>). Plan-first: `_ship_plan` returns a `(moves, warnings)` list and moves NOTHING; `cmd_ship` prints it + prompts; `_execute_ship` performs it; then `_reindex` (footage entered an indexed root).
- Project found by name (reuses `_find_stage_item`); footage located by parsing `Batch N Vid M` from the video name → `Batch_0N/Vid_0M`, else `--footage`. A missing half → warn + skip (never guesses). Overwrite → abort.
- The `(moves, warnings)` split is deliberate: a planned folder-watcher reuses `_ship_plan`/`_execute_ship` headless to do "drop file in 03_DELIVERED → auto-plan → approve → execute". The watcher MUST wait for the export to finish writing (file size stable) before planning, or it'll act on a half-written file.

**Hard rules:**
- Every clip exists in exactly ONE permanent location (`06_FOOTAGE_LIBRARY/`)
- `08_QUERY_PULLS/` is the ONLY place duplicates are tolerated — and only temporarily, until the edit ships
- `pull-cleanup` deletes pull folders after publish, restoring the no-duplication invariant

**Weekly workflow:**
- Automatic: any `index` or `pull` run creates this week's `W##_MMM-DD-DD/` folders first (lazy `ensure_week`). No manual Monday step. `create-week --week <date>` backfills other weeks.
- After editing + publishing a video: `python cli_index.py --client sai pull-cleanup` deletes the pull folder used for that edit
- Week numbering: W01 = ISO week of Apr 15, 2026 (Sai project Day 1). W01 label uses Apr 15-19 (partial week starting at project day 1)

**Cross-platform:**
- All paths use `pathlib.Path`, no drive-letter assumptions. Drive root is read from `<CLIENT>_LIBRARY_ROOT` env var (`.env` differs per machine: `/Volumes/Footage/Sai` on Mac, `D:/Sai` on Windows).
- All scripts force UTF-8 stdout/stderr (Windows defaults to cp1252).
- Folder names contain no spaces or non-ASCII (`W01_Apr-15-19` — hyphen-separated).
- **SQLite index stores POSIX-relative paths** (`05_FOOTAGE_LIBRARY/...`) so the same `.footage-index.sqlite` on the shared SSD works from either machine. `cli_index.py` resolves against the current machine's library root at read time. First run on the upgraded code (post-2026-05-02) auto-wipes any pre-migration DB containing absolute paths and rebuilds — symmetrical, runs once per machine, free.
- Walker filters Mac AppleDouble files (`._*`) and `.DS_Store` so they don't pollute the index when the drive is mounted on Mac.
