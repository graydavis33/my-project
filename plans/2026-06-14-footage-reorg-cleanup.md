# Footage Drive Reorganization & Cleanup — Plan

**Date:** 2026-06-14
**Status:** ✅ EXECUTED 2026-06-15. Drive root is back to the clean 9-folder scheme (+ protected `Rest of week` Ep2 raw); root strays + the `01_ORGANIZED` clog are drained; the `_TO_DELETE/` holding folder was emptied 2026-06-15 after Gray's final yes (~11GB reclaimed: 12 Ep1 render drafts — kept the newest, `Ep 1 Longform Doc Windows Final.mp4`, in `03_DELIVERED/episodes/` — plus junk + the stray `token.json` security item). NOTE: landing spots for the big moved items (Onboarding 94G, Longfrom Doc 57G, etc. in §6) were confirmed GONE from root/`01_ORGANIZED` but their destination folders were not all re-verified this session.
**Scope:** `D:/Sai/` on disk only. Pairs with the v3 code work (`plans/2026-06-03-footage-organizer-v3.md`) — the freeform-folder index change lands after the disk is clean.

---

## 0. PROTECTED — DO NOT TOUCH (Episode 2 documentary raw footage)

Per Gray (2026-06-14). These folders are **off-limits** to every phase — no move, no rename, no merge, no delete:
- `Rest of week/` (root, 5.8G — C2669+ raw)
- `01_ORGANIZED/2026-06-06`
- `01_ORGANIZED/2026-06-09`
- `01_ORGANIZED/2026-06-10`
- `07_QUERY_PULLS/EP2-arc-map/`

Note: 06-06/09/10 were renamed in Phase A from illegal-char names (`06"06"26` etc.) — folder names only changed, raw files 100% intact. Pending Gray's OK to keep the clean names vs revert.

## 1. Goal

Drain the clog and kill the strays so the drive matches the documented 9-folder scheme again. **No mass-moving of irreplaceable footage on guesses** — every judgment call is in the §6 table for Gray to confirm first.

## 2. Decisions locked

| Decision | Choice |
|---|---|
| Existing 154G AI-categorized library (`05`) | **Leave as-is.** Keep the 17 category folders. Add freeform folders alongside going forward (v3 index change supports it). No re-sort. |
| `misc` (40G dumping ground) | **Leave for now** (not re-filing this pass). |
| Execution | **Plan-first.** This doc, approved, then execute in safe verified batches. |
| Deletions | **Never silent.** Files only ever MOVE, unless Gray explicitly says delete. Junk goes to a `_TO_DELETE/` holding folder for his final yes. |

## 3. The documented target structure (what "clean" means)

```
D:/Sai/
  00_TEMPLATES/        templates, LUTs, title cards
  01_ORGANIZED/        STAGING ONLY — loose footage for the current shoot, drained regularly
  02_ACTIVE_PROJECTS/  <format>/  projects being edited now
  03_DELIVERED/        <format>/  finished published exports
  04_ARCHIVE/          <format>/  retired projects
  05_FOOTAGE_LIBRARY/  <category>/W##_*/  permanent reusable footage  ← left alone this pass
  06_ASSETS/           brand assets, fonts, music, SFX, thumbnails, PSDs
  07_QUERY_PULLS/      temp query results (just cleaned — only LinkedIn Photos + a few pulls left)
  08_AI_EDITS/         <pipeline>/<source>/  AI pipeline outputs
  .footage-index.sqlite
```
Format buckets in 02/03/04: `episodes/`, `shorts/`, `linkedin/` (+ `podcasts/` proposed, see §6).
**Nothing else lives at the drive root.**

## 4. The mess, itemized

**Root-level strays (don't belong):**
| Item | Size | Proposed home | Confidence |
|---|---|---|---|
| `Onbaording Videos/` | 94G | merge into ONE onboarding project location (active or archive) | NEEDS DISPOSITION |
| `All Broll/` (142 clips, old C07xx + phone + personal) | 9.8G | split: Sai b-roll → library; personal/junk → `_TO_DELETE/` | NEEDS REVIEW |
| `Podcasts/` (Adobe/Assets/Finals/Incoming) | 168M | `02_ACTIVE_PROJECTS/podcasts/` (new bucket) or archive | NEEDS DISPOSITION |
| `Screenshot 2026-05-04….png` | — | `_TO_DELETE/` | safe |
| `final thumbnail 2.psd`, `Untitled-3.psd` | — | `06_ASSETS/thumbnails/` or `_TO_DELETE/` | low |
| `token.json` | — | **SECURITY** — move off drive to a safe local spot, then likely delete | flag |

**`01_ORGANIZED/` clog (127G) — staging area full of un-drained shoots:**
| Folder | Size | What it is | Proposed | Confidence |
|---|---|---|---|---|
| `Longfrom Doc` | 57G | EP1 doc raw (doc IS delivered) | archive raw OR library | NEEDS DISPOSITION |
| `Batch 2` | 19G | batch shorts shoot | → `Batch_02/Vid_MM/` (v3 batch cmd) | NEEDS MAP |
| `Longfrom Pod` | 16G | pod multicam (synced already) | archive raw OR library | NEEDS DISPOSITION |
| `Founders Series Part 2` | 8.4G | founders shoot | active or archive | NEEDS DISPOSITION |
| `06"09"26` | 7.3G | raw daily shoot, **illegal name** | rename → `2026-06-09`, then file | rename safe |
| `Batch 1` | 7G | batch shorts shoot | → `Batch_01/Vid_MM/` | NEEDS MAP |
| `06"06"26` | 4.3G | raw daily, illegal name | rename → `2026-06-06` | rename safe |
| `2026-05-04` | 3.6G | raw daily | file into library/project | NEEDS DISPOSITION |
| `06"10"26` | 3.0G | raw daily, illegal name | rename → `2026-06-10` | rename safe |
| `affirmations` | 1.8G | affirmations shoot | active or archive | NEEDS DISPOSITION |
| `copy_0475….mov` | — | loose stray clip | identify + file or delete | low |

**`04_ARCHIVE/` — mixed scheme** (legacy named folders beside format buckets):
`Subway Cahllenge Day 1/2/3` (misspelled), `Day in the Life`, `Longform`, `Paid Ads`, `Photoshop`.
→ Proposed: leave legacy archive content in place (it's already archived), just fix the `Cahllenge` typo. Low priority. CONFIRM.

**Other tidy-ups:**
- `02_ACTIVE_PROJECTS/`: stray `Photoshop/`, `affirmations/` → fold into proper buckets.
- `03_DELIVERED/`: loose `Ep 1 Longform Doc Draft 4.mp4` at top → `03_DELIVERED/episodes/`; `Onboarding/` → consolidate with the 94G stray.
- `08_AI_EDITS/`: `Untitled - Higgsfield.html` + `_files/` → `_TO_DELETE/`.
- `05_FOOTAGE_LIBRARY/`: stray `old-broll/` (non-week folder) → confirm keep or fold.

## 5. Execution phases (safe → judgment-heavy)

**Phase A — Zero-risk quick wins (no footage moves):**
1. Create `_TO_DELETE/` holding folder at root.
2. Rename the 3 illegal date folders (`06"09"26` → `2026-06-09`, etc.).
3. Move loose junk files (screenshot, html+_files, Higgsfield junk) → `_TO_DELETE/`.
4. Handle `token.json` (security) — move off drive.
5. Move loose `Ep 1 … Draft 4.mp4` → `03_DELIVERED/episodes/`.
6. Fix `Subway Cahllenge` typo.

**Phase B — Relocate strays (per §6 dispositions):**
7. Consolidate the two Onboarding locations.
8. `Podcasts/` → its decided home.
9. `All Broll/` review — Sai b-roll vs personal/junk split.

**Phase C — Drain `01_ORGANIZED` backlog (per §6 dispositions):**
10. Batch 1 / Batch 2 → `Batch_NN/Vid_MM/` (uses the v3 `batch` command once built, or manual now).
11. Each long-form/pod/doc/founders/affirmations/daily shoot → archive / active / library per Gray's call.

**Phase D — Project-bucket tidy:**
12. Fold stray `Photoshop`/`affirmations` in 02 into buckets.

After each phase: print before/after counts + sizes; verify nothing lost.

## 6. Dispositions Gray must confirm (fill these in)

For each un-drained shoot — is it **DONE** (→ archive raw, or file b-roll into library) or **STILL ACTIVE** (→ active projects)?

| Item | DONE or ACTIVE? | Where? |
|---|---|---|
| `Onbaording Videos` (94G) + `03_DELIVERED/Onboarding` | ? | |
| `Longfrom Doc` raw (57G) | ? | |
| `Longfrom Pod` raw (16G) | ? | |
| `Founders Series Part 2` (8.4G) | ? | |
| `Podcasts/` | ? | |
| `affirmations` | ? | |
| `2026-05-04` daily | ? | |
| Batch 1 → Vid map | provide e.g. `1:C2493-C2495 2:…` | |
| Batch 2 → Vid map | provide map | |
| `All Broll`: keep personal clips? | ? | |
| `04_ARCHIVE` legacy folders: leave as-is? | proposed YES | |

## 7. Safety protocol

- All operations are **moves within `D:/Sai`** (same drive = fast, no copy). Footage is never deleted by this plan.
- Deletion candidates go to `_TO_DELETE/`; Gray gives a final yes before it's emptied.
- Before/after file counts logged per phase — a phase that loses a file aborts.
- The SQLite index (`05` only) is re-built (`cli_index … index`) after moves so it matches disk. Library isn't moving, so the index stays valid throughout.
- Re-index is free + ~30s; folders are the source of truth.

## 8. Pairing with v3 code

Once the disk is clean and Gray's freeform folders exist, the v3 `_category_from_path` change (treat ANY folder under `05_FOOTAGE_LIBRARY/<name>/<week>/` as the category) makes those folders index + pull correctly. The `batch` command (v3 Workstream 1) is what files Batch 1/2 in Phase C.
