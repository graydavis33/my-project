# Footage Organizer v4 — Batch Content System

**Date:** 2026-06-18
**Status:** Plan — awaiting Gray's go-ahead on Phase 1
**Tool:** `python-scripts/footage-organizer/`

---

## Why this change

Filming shifted from **one video a day** to **batch shoots**:
- Multiple shorts filmed in one session.
- Often **two cameras** — Sony A-cam (`C####.MP4` + `C####M01.XML`) and Canon B-cam (`MVI_####.MP4`).
- **B-roll mixed into the same sessions** (sometimes its own folder, sometimes loose).
- Everything shot **horizontal** now, so b-roll is reusable for **both shorts and long-form**.

The current `batch` command only handles one camera and doesn't separate b-roll. This redesign makes
intake handle the new reality, and adds a multi-trait **tag/search** layer so footage is findable by
action / location / emotion / object instead of a single category folder.

---

## Decisions locked with Gray (2026-06-18)

- **Two cameras → paired per video:** `Batch_NN/Vid_MM/A-cam/` + `Vid_MM/B-cam/`. Camera **auto-detected
  by filename** (Sony `C####` = A-cam, Canon `MVI_####` = B-cam) — no labeling.
- **Findability = tags, not folders.** Each reusable clip is tagged once; pull by any combination. No
  duplicate files (honors the no-duplication rule + saves SSD space).
- **Tag scheme:**
  - Footage **with Sai** → `emotion` (happy / sad / angry / stoic …) + `action` (walking / eating /
    cooking …) + `location` (stairs / bedroom / Times Square …) + week.
  - Footage **without Sai** (pure b-roll) → `object` (coffee cup / cars / buildings …) + `location` + week.
  - **Emotion present = Sai present.** No separate "with Sai" flag — an emotion tag IS the signal.
- **Auto-tagging by AI.** Re-enable the paused Haiku Vision clip-watcher, expanded to output these traits.
  ~$0.003/clip, cached (re-runs free).
- **"Filmed together" = a mix:** sometimes clean separate clips (sorting handles it), sometimes one long
  clip covering several videos (needs in-clip splitting — deferred to Phase 2.5).

---

## Phase 1 — Intake & sorting (build + run TODAY)

**Goal:** get Batch 3, Ep 2, and the loose b-roll filed correctly so editing isn't blocked.

Enhance the `batch` command in `cli_index.py`:

1. **Camera auto-routing.** A Vid's mapped clips can include both `C####` and `MVI_####`; the tool files
   each into the `A-cam/` or `B-cam/` subfolder by prefix. (Extend `_expand_clip_segment` to accept the
   `MVI_` underscore prefix + ranges like `MVI_5040-MVI_5042`.)
2. **B-roll routing.** New `--broll <folder>` moves every clip in a folder →
   `05_FOOTAGE_LIBRARY/b-roll/<week>/` (a stable home; Phase 2 tags add the real findability in the index
   without moving files). "b-roll" = Gray's word for reusable footage, which may include Sai.
3. **Safe names + cleanup.** Auto-fix colon/space folder names; remove emptied source folders after moving.
4. **Plan-first safety.** Show the full move plan and require confirmation before moving real footage
   (mirrors `ship`). `--yes` to skip.
5. **Tests** mirroring `test_batch.py`: camera routing, b-roll routing, name-safety, idempotent re-run.

**Live runs after tests pass (each shown as a plan first):**
- **Batch 3:** A-cam C2738–45 + B-cam MVI_5040–46 → Vid folders (Gray provides the per-Vid grouping).
- **B-roll:** `B-roll 06:17:26` (C2724–36, C2746) → `05_FOOTAGE_LIBRARY/b-roll/<week>/`.
- **Strays:** loose `C2737.MP4` at root; older `06:15:26-06:16:26` (C2687+) and `Rest of week` (C2669+).
- **Ep 2 interview** (C2747–52 A-cam + MVI_5047–53 B-cam) — this is **long-form, not a shorts batch**, so
  it files as an episode project, not Vid folders. Handle separately (see open items).

---

## Phase 2 — AI tag + search (build next; can start today)

1. **Vision prompt** (`analyzer.py`): structured output `{emotion?, action?, location, objects[]}` — emotion
   only when Sai is in frame.
2. **Index schema** (`index.py`): add `emotion, action, location, objects` columns; non-destructive
   `ALTER TABLE` migration (same pattern as `batch_num`).
3. **Tag command:** `tag` (or `index --vision`) runs Vision on untagged library clips; caches by file hash;
   Haiku; only new clips cost money.
4. **Pull filters** (`pull.py` + CLI): `pull --emotion stoic --location "times square" --action walking
   --object "coffee cup"`; combine freely.
5. **Tests + a small live sample** (tag ~5 clips, eyeball accuracy) before tagging everything.

---

## Phase 2.5 — In-clip splitting (later, only if a real clip needs it)

For the "one long clip covers several videos" case: a `--split` that cuts a clip at given timecodes into
per-Vid pieces. Build only when it actually comes up.

---

## Concerns / open items

- **Disk:** two cameras doubles footage on an SSD that already fills up. Retention rule (keep A-cam selects,
  drop raw B-cam after ship?) — decide at first ship; default = archive both.
- **Week label format:** keep existing `W##_MMM-DD-DD` (already across the library, sorts chronologically)
  vs Gray's `06/14/26-06/20/26`. Recommend keeping `W##_MMM-DD-DD`; his example = `W10_Jun-14-20`.
- **Ep 2 is long-form,** not a shorts batch — files as an episode project (2-cam), reusing the camera
  auto-routing but not the Vid scheme.
- **Orientation/`format` column** in the index is now vestigial (all horizontal); superseded by tags.
- **Legacy 17-category folders + 841 indexed clips** stay as-is; optionally back-tag with Vision later.

---

## Files touched

| File | Change |
|------|--------|
| `cli_index.py` | batch camera-routing + `--broll` + plan-first; new `tag` cmd; pull filters |
| `config.py` | camera filename patterns; tag vocab |
| `analyzer.py` | expanded Vision prompt (Phase 2) |
| `index.py` | tag-column schema migration (Phase 2) |
| `pull.py` | tag filters (Phase 2) |
| `tests/` | extend `test_batch.py`; new `test_tags.py` |
| docs | `README.md`, tool `CLAUDE.md`, `workflows/footage-organizer.md`, `decisions/log.md` |
