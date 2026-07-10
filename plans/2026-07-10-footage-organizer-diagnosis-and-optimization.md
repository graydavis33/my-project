# Footage Organizer — Diagnosis & Optimization Plan

**Date:** 2026-07-10
**Status:** Plan — awaiting Gray's go-ahead (no code touched yet, per the no-silent-tool-changes rule)
**Tool:** `python-scripts/footage-organizer/`

---

## Health check (what's actually true today)

- Tests: **158/158 pass** in 0.6s. Code is not broken.
- Live index: 899 clips, schema + all tag/batch columns and SQL indexes in place.
- Drive mounted, `.env` correct, structure guard working.

The tool is healthy. The problems are **speed, staleness, and one missing feature** — not bugs.

---

## Diagnosis — 5 findings, ranked

### 1. The gating feature is missing: `pull` cannot filter by batch
The whole point of the "new version" (memory `fo-new-version-focus`, 2026-06-18) was batch
filtering, and Batch 3 auto-editing is gated on it. The database HAS `batch_num`/`vid_num`
columns and `index.query()` accepts them — but the `pull` CLI never exposes them. There is
no `--batch` / `--vid` flag. The feature is 95% built and the last 5% (two `add_argument`
lines + wiring) never happened.

Also: only Batch 3 (60 clips) has batch numbers in the index. Batches 1/2/4/5 footage was
filed under other schemes, and `_BATCHES` under `05_FOOTAGE_LIBRARY` is index-skipped by
design — so "pull batch N" only means anything for batches still sitting in `01_ORGANIZED`.

### 2. Re-indexing is ~20x slower than it needs to be → the index is chronically stale
The index is 2 weeks stale (newest filmed_date 2026-06-24; July footage exists on the drive).
This same "stale index" pain has been logged at least 3 times before (2026-06-05, 06-20, etc.).
Root cause is that `index` is slow AND fully manual, so it doesn't get run.

Why it's slow — `_reindex()` in `cli_index.py`:
- **4 separate ffprobe subprocess launches per clip** (resolution, duration, shoot date,
  orientation). Measured on the real SSD: 0.34s for the 4 calls vs **0.063s for one
  combined call** returning all the same data.
- **No incremental skip.** Every run re-probes all 899 clips even though ~0 changed.
  Files never change in place in this library — a (size, mtime) match means the row is
  already correct.
- **Reads 1MB per file for sha1 every run** (fingerprint never changes for an unchanged file).
- **One new SQLite connection per clip** (`index.upsert` opens/commits per row).
- Everything is serial; the disk sits idle between subprocess spawns.

Net: a full index ≈ 5+ minutes today. Incremental should be **~5 seconds** when nothing
changed, which makes finding #3 possible.

### 3. Staleness fix: auto-refresh the index before every `pull`
Once incremental indexing is cheap, `pull` (and `tag`) can run it automatically at start —
same pattern as the existing `ensure_week` lazy call. The stale-index class of problem
disappears permanently. No daemon, no scheduler — respects the one-scheduler rule and the
right-size-automation lesson (on-demand beats a watcher).

### 4. Repo hygiene: generated files are committed to git
Tracked in git right now: `.footage-index.sqlite` (a stray **0-byte** DB in the tool folder —
the real one lives at the library root), `.tag-cache.json` (136KB, churns on every tag run),
`.cache.json`, `.tmp_libhoriz_results.txt`. All generated artifacts; none belong in the repo.
Also ~900 lines of one-time `migrate_*.py` scripts (all completed months ago) cluttering the
tool folder.

### 5. v4 Phase 1 (two-camera batch intake) was planned but never built
The 2026-06-18 v4 plan's Phase 1 — `batch` auto-routing Sony `C####` → `A-cam/`, Canon
`MVI_####` → `B-cam/`, plus `--broll` routing — has **zero code** in `cli_index.py` (no MVI_
reference anywhere). Batch 3 got filed by hand instead. If future batches are 2-camera
(they are, per the multicam pipeline), this gap costs manual filing time every shoot.

Minor notes (no action needed now): `codec` column is always `""` and `format` is vestigial
(superseded by `orientation`); the launchd sweep plist is an uninstalled template (fine —
sweep runs manually).

---

## The Plan

### Phase 1 — Batch filtering (the unblocker) — TINY
1. Add `--batch N` and `--vid M` to the `pull` parser; pass through to `index.query()`
   (which already supports them).
2. Add a `list-batches` helper (or extend `pull --batch` dry output) showing which
   batch/vid combos exist in the index and clip counts.
3. Tests mirroring `test_pull.py`.

**Unblocks Batch 3 Vids 3–13 auto-editing immediately.**

### Phase 2 — Index performance (the optimization)
1. **One ffprobe call per clip**: single `-show_entries
   stream=width,height:stream_tags=rotate:stream_side_data=rotation:format=duration:format_tags=creation_time`
   JSON call; parse all five values from it. Keep the 20s timeout + "unknown" fallback.
2. **Incremental scan**: add `size_bytes` + `mtime` columns (non-destructive ALTER, same
   pattern as `batch_num`). On scan: if (path, size, mtime) matches the existing row,
   skip probing entirely — but still re-derive path-based fields (category, batch/vid)
   in SQL-only form since folder moves change the path anyway (a moved file = new path =
   full probe; acceptable).
3. **Parallel probing**: `ThreadPoolExecutor(max_workers=8)` for the probe step
   (subprocess-bound, threads are safe). Print progress every 50 clips.
4. **One DB connection per run**: batch the upserts in a single transaction
   (`executemany` or reused connection), instead of connect-per-clip.
5. Re-run the full suite + a live timed before/after on the real library.

**Expected: full cold re-index ~5 min → under 1 min; no-change re-index → seconds.**

### Phase 3 — Auto-fresh index
1. `pull` and `tag` call the (now cheap) incremental `_reindex` at start, gated behind
   a `--no-index` escape hatch. Print one line: "index refreshed (+N new, -M removed)".
2. Update README + tool CLAUDE.md + `workflows/footage-organizer.md` same commit.

### Phase 4 — Hygiene (quick, zero risk)
1. `git rm --cached` + gitignore: `.footage-index.sqlite`, `.tag-cache.json`,
   `.cache.json`, `.tmp_libhoriz_results.txt`; delete the stray 0-byte DB and
   `.tmp_libhoriz_results.txt` from disk.
2. Move the 5 completed `migrate_*.py` scripts to `python-scripts/_archive/footage-organizer-migrations/`.

### Phase 5 (OPTIONAL — Gray decides) — v4 Phase 1 camera routing
Build the 2026-06-18 plan's two-camera intake: `batch` files `C####` → `Vid_MM/A-cam/`,
`MVI_####` → `Vid_MM/B-cam/`; `--broll <folder>` routes to `05_FOOTAGE_LIBRARY/b-roll/<week>/`;
plan-first confirmation. Only worth it before the next 2-camera batch shoot is filed.

---

## Order & effort

| Phase | What | Effort | Risk |
|---|---|---|---|
| 1 | `pull --batch/--vid` | simple | none — additive flags |
| 2 | fast incremental index | moderate | low — schema ALTER is the proven pattern; full test suite + live timing |
| 3 | auto-refresh on pull | simple | low — escape hatch included |
| 4 | git hygiene + archive | simple | none |
| 5 | camera routing (optional) | moderate | low — plan-first moves |

Phases 1–4 are one focused session. Phase 5 is its own go/no-go.
