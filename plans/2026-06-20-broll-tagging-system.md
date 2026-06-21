# B-Roll Tagging System (Footage Organizer v4 — b-roll half)

**Date:** 2026-06-20
**Status:** Plan — awaiting Gray's go-ahead
**Tool:** `python-scripts/footage-organizer/`
**Supersedes the b-roll portions of** `plans/2026-06-18-footage-organizer-v4-batch-content.md` (the A/B-cam batch half of that plan is already handled by `ship` → `_BATCHES`).

---

## Goal

Replace the 17 content-category folders with a single **`b-roll/` library findable by tags** (emotion / action / location / object) instead of by folder. Gray tags via a local web dashboard that plays the full clip; AI (Opus) pre-fills the objective tags.

## Decisions locked with Gray (2026-06-20)

- **A/B-cam interview footage is NEVER b-roll.** It lives only in `05_FOOTAGE_LIBRARY/_BATCHES/Batch_NN/Vid_MM/` (filed by `ship`), stays out of the tag/filter system, and is never confused with b-roll. The b-roll system below touches only `b-roll/`.
- **Flatten everything reusable into `b-roll/`** — every clip from all 17 category folders + Gray's freeform folders moves into `05_FOOTAGE_LIBRARY/b-roll/<week>/`, regardless of its old category. Categories become tags, not folders. (`_BATCHES`, `_TO_SORT`, and other `_`-prefixed helpers are excluded.)
- **Week folders preserved both ways:**
  - Past b-roll keeps its **original** week — a clip in `…/<category>/W05_May-11-17/` moves to `b-roll/W05_May-11-17/`. Week comes from the source folder name; if the source has no week folder (freeform), derive it from the clip's `filmed_date` (index), else ffprobe `creation_time`. **No dates lost.**
  - New weeks auto-create via the existing lazy `ensure_week` (already runs on `index`/`pull`); new b-roll drops into the current week folder.
- **Tag scheme:**
  - **With Sai** → `emotion` + `action` + `location` + week.
  - **Pure b-roll** → `object` + `location` + week.
  - **Emotion present = Sai present** (no separate flag).
- **Model:** `claude-opus-4-8` for the initial tagging pass (strong model while building the data set, ~$5–13 one-time for the whole library at ~$0.015/clip); drop to `claude-haiku-4-5` for incremental tagging of new clips later (~$0.003/clip). Cached by file hash — re-runs are free.
- **Tagging dashboard = a local web page** served by a Python stdlib server (the `story-arc-board` pattern). Grid of thumbnails + an inline HTML5 **video player that scrubs the full clip** + editable tag chips + shift-select bulk-apply by shoot. Saves straight to the index. NOT HyperFrames, NOT Claude Code.
- **Division of labor:** AI pre-fills location/action/objects (+ a first-guess emotion); Gray reviews and owns emotion, fixing the occasional wrong location. Bulk-apply by shoot since clips from one session share location/vibe.
- **AI b-roll→script matching stays deferred** (separate from this). This is findability/tagging, not auto-injecting picks into scripts.

## Tag vocabulary (seed — Gray can edit; controlled lists keep filtering reliable)

- **emotion:** happy, excited, stoic, focused, stressed, tired, sad, angry, confident, reflective
- **action:** walking, talking, eating, drinking, cooking, working, filming, driving, sitting, exercising, on-phone, presenting
- **location:** seed from real shoots (NYC street, office, bedroom, kitchen, gym, cafe, Times Square, subway, rooftop, …) — freeform allowed, autocompletes from existing values
- **object:** freeform (coffee cup, laptop, car, building, sign, desk, food, …), autocompletes

`emotion`/`action` apply only when Sai is in frame; `object` for clips without him. All multi-valued where it makes sense (a clip can have several objects).

**Vocabulary is user-extensible (not a locked menu).** Every tag field in the dashboard is a type-to-add box with autocomplete: typing an existing value suggests it (prevents duplicate spellings like happy/Happy/joyful); typing a NEW value creates it on the spot and adds it to the vocabulary for all future clips. New tags persist to `tagger/vocab.json` so they survive across sessions and autocomplete everywhere. The seed lists above are just a starting point so the boxes aren't blank — Gray grows the vocabulary organically while tagging; no need to predefine everything.

---

## Phase 1 — Consolidate into `b-roll/<week>/` (build + run first)

**`consolidate-broll` command** in `cli_index.py`:
1. Walk every clip under `05_FOOTAGE_LIBRARY/<category>/…` (all 17 + freeform), skipping `_`-prefixed folders.
2. For each clip, compute its **target week**: source week-folder name if present → else `filmed_date` from the index → else ffprobe `creation_time`.
3. Plan the move to `05_FOOTAGE_LIBRARY/b-roll/<week>/<filename>` (Sony sidecars move with their clip).
4. **Plan-first:** print the full move plan (counts per week, any clips whose week couldn't be derived) and require confirmation (`--yes` to skip). Mirrors `ship`.
5. Execute pure moves — never overwrite, never delete; on a filename collision across categories, report and skip (don't clobber).
6. Re-index so paths + the new `category="b-roll"` are correct.
7. Remove emptied source category/week folders.

Tests (mirror `test_batch.py`): week-from-source-folder, week-from-filmed-date fallback, sidecar move, collision skip, idempotent re-run, `_`-folder exclusion.

`_category_from_path` already treats the first folder under `05_FOOTAGE_LIBRARY/` as the category, so post-move every clip indexes as `b-roll` automatically.

## Phase 2 — Tag schema in the index

- `index.py`: add `emotion, action, location, objects` columns via non-destructive `ALTER TABLE ADD COLUMN` (same pattern as `batch_num`/`vid_num`). `objects` stored as a delimited string or JSON.
- New `idx_tags` created inside `_migrate` (after the columns exist), never in `_SCHEMA`.
- Tags are index-only metadata (no extra folders), so the no-duplication rule is untouched.

## Phase 3 — Vision tagging (Opus 4.8)

- `analyzer.py`: structured-output prompt returning `{emotion?, action?, location, objects[]}` — emotion/action only when Sai is in frame. Use `claude-opus-4-8` with `output_config.format` (json_schema) for clean validated tags. 4 frames/clip (existing extractor).
- New `tag` command: runs Vision on untagged `b-roll` clips, caches by file hash (`.cache.json`), writes tags to the index. `--model` flag (default `claude-opus-4-8`; pass `claude-haiku-4-5` for cheap incremental runs).
- First run on a ~5-clip sample to eyeball accuracy before tagging everything; then full run (~$5–13 one-time).

## Phase 4 — Web tagging dashboard (local)

`python-scripts/footage-organizer/tagger/server.py` (stdlib `http.server`, the story-arc-board pattern):
- **Grid view:** thumbnail per b-roll clip (ffmpeg, auto-rotated), AI-prefilled tag chips, grouped/sortable by week + shoot.
- **Full-clip review:** click a clip → inline HTML5 `<video>` streaming the real file from the server (HTTP range requests) so Gray can **play/scrub the entire clip** before tagging.
- **Editing:** click chips to set/clear emotion/action/location/object; **shift-select** multiple clips → bulk-apply a tag (one session = one location/vibe → a handful of decisions, not hundreds); location/object autocomplete from existing values.
- **Save:** POST writes tags to the SQLite index.
- Run `python server.py` → `localhost:<port>`. All endpoints tested against generated test clips.

## Phase 5 — Pull by tag

- `pull.py` + CLI: `pull --emotion stoic --location "times square" --action walking --object "coffee cup"` — any combination, AND-combined; reuses the existing `07_QUERY_PULLS/<slug>/` output + the 7-day auto-sweep.

---

## Open items / notes

- **Week label format** stays `W##_MMM-DD-DD` (already across the library, sorts chronologically; W01 = ISO week of 2026-04-15).
- **`format`/orientation column** is now vestigial (all horizontal) — leave it, superseded by tags.
- **Legacy interview-solo/duo clips:** included in the flatten per "everything reusable" — they become b-roll and get tagged like anything else. (Flag if Gray wants them carved out instead.)
- **Disk:** consolidation is moves within one drive — no extra space used; emptied folders cleaned up.
- **Docs to update in the same commits:** `README.md`, tool `CLAUDE.md`, `workflows/footage-organizer.md`, `decisions/log.md`, memory.

## Files touched

| File | Change |
|------|--------|
| `cli_index.py` | `consolidate-broll` (plan-first move + reindex); `tag` command; pull-by-tag wiring |
| `config.py` | tag vocab seed lists; `b-roll` folder constant |
| `index.py` | tag-column schema migration + `idx_tags` |
| `analyzer.py` | Opus structured-output tagging prompt |
| `pull.py` | tag filters |
| `tagger/server.py` + assets | local web tagging dashboard (grid + full-clip player + bulk tag) |
| `tests/` | `test_consolidate.py`, `test_tags.py` |
| docs | README, tool CLAUDE.md, workflows SOP, decisions log, memory |
