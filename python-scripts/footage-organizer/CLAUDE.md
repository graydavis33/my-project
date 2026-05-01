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

## Disk Structure (2026-05-01)

**Library root (`/Volumes/Footage/Sai/` on Mac, `D:/Sai/` on Windows):**
```
00_TEMPLATES/                                    project templates, LUTs, title cards
01_RAW_INCOMING/<date>/                          temp card dumps, deleted after organize
02_ORGANIZED/<category>/<date>/                  AI-sorted, awaiting edit + archive
03_ACTIVE_PROJECTS/                              active editing projects
04_DELIVERED/                                    finished published exports by format
05_ARCHIVE/                                      retired projects
06_FOOTAGE_LIBRARY/<category>/W##_MMM-DD-DD/     permanent reusable footage, weekly
07_ASSETS/                                       brand assets, fonts, music, SFX
08_QUERY_PULLS/<slug>/                           temp query results — deleted after publish
09_AI_EDITS/<source>/<pipeline>/                 AI pipeline outputs grouped by source clip
.footage-index.sqlite                            SQLite index of all clips
```

**Hard rules:**
- Every clip exists in exactly ONE permanent location (`06_FOOTAGE_LIBRARY/`)
- `08_QUERY_PULLS/` is the ONLY place duplicates are tolerated — and only temporarily, until the edit ships
- `pull-cleanup` deletes pull folders after publish, restoring the no-duplication invariant

**Weekly workflow:**
- Every Monday: `python cli_index.py --client sai create-week` creates `<category>/W##_MMM-DD-DD/` under all 17 categories
- After editing + publishing a video: `python cli_index.py --client sai pull-cleanup` deletes the pull folder used for that edit
- Week numbering: W01 = ISO week of Apr 15, 2026 (Sai project Day 1). W01 label uses Apr 15-19 (partial week starting at project day 1)

**Cross-platform:**
- All paths use `pathlib.Path`, no drive-letter assumptions. Drive root is read from `<CLIENT>_LIBRARY_ROOT` env var (`.env` differs per machine: `/Volumes/Footage/Sai` on Mac, `D:/Sai` on Windows).
- All scripts force UTF-8 stdout/stderr (Windows defaults to cp1252).
- Folder names contain no spaces or non-ASCII (`W01_Apr-15-19` — hyphen-separated).
