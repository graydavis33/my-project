# Footage Organizer v3 — Plan

**Date:** 2026-06-03
**Status:** IN PROGRESS — **Phase 1 (lazy week creation) shipped 2026-06-10**. **Phase 2 (freeform-folder indexing + ensure_week freeform discovery) shipped 2026-06-15** (tests 34/34). Open questions answered 2026-06-15: batch folders → `01_ORGANIZED/Batch_NN/Vid_MM`; forgotten moves → ACTIVE→DELIVERED, DELIVERED→ARCHIVE, pull-cleanup; library → keep 17 as-is + seed freeform starter set. Phases 3 (batch cmd + schema) & 4 (stage-transition cmds) remain. Pairs with the disk cleanup in `plans/2026-06-14-footage-reorg-cleanup.md`.
**Tool:** `python-scripts/footage-organizer/`

---

## Goal

Make the footage organizer fit the batch system and stop relying on Gray's memory. Keep the system + flow Gray likes; change three things: (1) batch shoots organize by Batch/Vid, (2) commands handle the moves/folders themselves so steps can't be forgotten, (3) the footage library goes manual-categorized (Gray's own folders) until the AI is accurate enough — and Gray's manual sorts become the data that earns the automation back.

## Decisions locked (from 2026-06-03 Q&A)

| Decision | Choice |
|---|---|
| Automation style | **Smart commands** — no background app. Commands auto-create folders + run a stage's moves in order. |
| Library categories | **Gray's own freeform folders.** AI auto-labeling paused. Manual placements logged as training data. |
| Batch → Vid mapping | **Gray gives a quick map** after each shoot (e.g. `1:C2493-C2495`). 3 hook takes live inside their Vid folder. |
| Cost during this phase | Vision (Haiku) paused for library + skipped for batch → ~$0 API spend until the classifier is re-enabled. |

---

## Workstream 1 — Batch footage by Batch / Vid

**New command** (smart — does the whole stage in order):
```
python cli_index.py --client sai batch --num 2 --from "01_ORGANIZED/2026-06-07" \
    --map "1:C2493-C2495 2:C2496-C2498 3:C2500-C2502"
```
What it does, in order:
1. Ensure this week's folders exist (lazy create-week).
2. Create `Batch_02/Vid_01/`, `Vid_02/`, … under the batch location.
3. Move each mapped clip range into its Vid folder (the 3 hook takes land together).
4. Re-index (tags these clips `batch_num=2, vid_num=1…`).
5. Print a summary + anything unmapped (so no clip is silently left behind).

- **No Vision** on batch footage — it's mapped, not classified.
- Unmapped clips in the source are reported, never dropped.

**Open question #1 — where do batch folders live on disk?** Proposal A (aligns with the editing SOP): `01_ORGANIZED/Batch_NN/Vid_MM/`. Proposal B: `02_ACTIVE_PROJECTS/shorts/Batch_NN/Vid_MM/`. Need Gray's pick.

## Workstream 2 — Smart commands (kill the "I forgot" problem)

- **Lazy week creation:** every command (`organize`, `batch`, `index`, `pull`) calls `ensure_week(today)` first. Folders appear the moment you touch a week — you never run `create-week` by hand again. (`create-week` stays as a manual backfill option.)
- **One command = one whole stage.** Each command chains its own follow-up moves (e.g. `batch` re-indexes itself; `organize` re-indexes itself) so there's no "now remember to run index" step.
- **Stage-transition helper** for the moves Gray forgets (ACTIVE → DELIVERED → ARCHIVE, pull-cleanup, etc.) — exact set pending Open question #2.

**Open question #2 — which moves do you keep forgetting?** List them (e.g. "moving a finished video from ACTIVE_PROJECTS to DELIVERED", "running pull-cleanup", "creating the week") so I bake each into a command instead of leaving it to memory.

## Workstream 3 — Manual library categorization (AI paused)

- **Pause Vision auto-filing** for non-batch footage. New `organize` behavior: set up the date/format landing spot and let Gray hand-place clips into folders he names. (The old Vision path stays in the code, just off by default, so we can flip it back on later.)
- **Index accepts freeform folders:** change `_category_from_path` so ANY folder name under `05_FOOTAGE_LIBRARY/<name>/<week>/` is treated as the category — not just the fixed 17. So Gray's own folders index + pull correctly.
- **Capture training data automatically:** every indexed clip records `(clip → the folder Gray put it in)`. That builds the labeled set (same shape as the existing `eval.py` CSV) so when we re-enable the classifier later, it learns Gray's taxonomy and we can measure accuracy against his real choices.
- **Keep** the date structure + long-form/short-form split (unchanged).

**Open question #3 — freeform folders: define them up front, or make them as you go?** Either works for the index; just changes whether I seed a starter set of folder names or leave it fully ad hoc.

## Workstream 4 — Auto weekly folders

Covered by Workstream 2's lazy `ensure_week`. No separate scheduler (matches your "smart commands" choice and the one-scheduler rule). `create-week` remains for backfilling a past/future week on demand.

---

## Files touched (estimate)

| File | Change |
|---|---|
| `cli_index.py` | New `batch` command; `ensure_week()` helper called by every command; freeform-category indexing |
| `index.py` | Schema: add `batch_num`, `vid_num` columns; bump schema version for safe rebuild |
| `config.py` | Batch folder constant(s); flag to disable Vision auto-filing |
| `main.py` | `organize` manual-mode default (Vision off); auto re-index after organize |
| `week_utils.py` | (likely no change — reuse `week_label_for`) |
| `README.md` + folder `CLAUDE.md` | Document v3 commands + the manual-categorization phase |
| `workflows/footage-organizer.md` | Update SOP |

## Cross-machine safety (the real risk)

The index stores POSIX-relative paths and already auto-wipes legacy absolute-path DBs. Adding `batch_num`/`vid_num` columns is a **schema change** — to stay safe on both machines I'll bump a `schema_version` and rebuild on mismatch (rebuild is ~30s and free). This keeps the same "first machine to run the new code rebuilds; others short-circuit" guarantee. No data loss — folders are the source of truth; the index is derived.

## Suggested phasing (each shippable on its own)

1. ✅ **Lazy week creation** (Workstream 2 core) — DONE 2026-06-10. Smallest, highest daily relief, no schema change.
2. **Manual categorization + freeform index** (Workstream 3) — unblocks you hand-sorting today.
3. **Batch command** (Workstream 1) — needs the schema change; do once #1/#2 are proven.
4. **Stage-transition helpers** (Workstream 2 rest) — after you answer #2.

## Out of scope (future)

- Re-enabling the Vision classifier (it comes back once the manual data clears an accuracy bar).
- The AI B-roll matcher (separate tool idea; this just makes the index ready for it).
- Any background/watcher automation (explicitly not chosen).
</content>
