# Batch Pipeline — integrate the proven manual trim/sync recipe

**Date:** 2026-06-21
**Goal:** Replace `orchestrate.py`'s fully-automatic sync+select+cut with the proven manual-recipe shape (`_prep.py` / `_cut_preview.py` / `build_review.py` from `01_ORGANIZED/Batch_03/Vid_09` + `Vid_13`), which produced Gray's "best first-try trim ever." Do NOT build a new tool — fold it into `python-scripts/batch-pipeline/`.

**Decision (Gray, 2026-06-21):** keep a human-in-the-loop. New shape = **Prep → (Gray reviews/edits SEGMENTS) → Render**.

## Why
- `sync.py` uses a single 30s-window xcorr, no dominance/confidence check → can lock the wrong peak.
- `select.py` auto-picks editorial ranges from heuristics → this is the part that was worse than the manual cut. Editorial segment choice is human judgment; demote select to a *seed proposal*.
- The manual recipe: full-clip envelope xcorr + bandpassed (300–3000 Hz) verification (confirm dominant lag), B-cam word-level Whisper transcript, hand-built sentence-boundary SEGMENTS, HyperFrames trim-review BEFORE final render, per-segment ProRes 422 reels (concat-copy clean).

## New UX
| Phase | Command | Does |
|---|---|---|
| Prep | `orchestrate --batch N --video M --prep` | verify-synced offset (envelope + bandpass), transcribe B-cam word-level, write editable `Vid_MM/SEGMENTS.json` (seeded by select.py as a proposal, with the transcript inline as comments/text), auto-build a HyperFrames trim-review comp under `web-apps/hyperframes/sai-bNvMM-trim-review/` |
| Review | (Gray) | open review studio, edit `SEGMENTS.json` in/out times |
| Render | `orchestrate --batch N --video M --render` | read SEGMENTS.json → per-segment ProRes 422 A/B reels (B-cam audio on both, frame-locked 23.976) → H.264 angles → export to `08_AI_EDITS/shorts/Batch_NN/B3_VMM - <title>/ANGLES/` + `_INFO.txt`; keep ProRes masters in `Vid_MM/Cut/` |

## Tasks (subagent-driven, two-stage review each)
1. **sync.py: add `verify_offset()`** — full-clip envelope xcorr + bandpassed-speech xcorr returning (offset, peak, dominance ratio vs runner-up). `compute_offset` stays for back-compat but `--prep` uses verify. Tests: synthetic delayed signal → correct lag + high dominance.
2. **prep phase** — `orchestrate --prep`: sync(verify) → transcribe B-cam word-level → seed SEGMENTS.json from select.py → write it human-editable (segments with in/out/text + a `dropped` log). No cut/caption/package.
3. **trim-review builder** — port `build_review.py` into the pipeline (`review.py`): from SEGMENTS.json + a 720p B-cam proxy, generate the HyperFrames comp (read-along lower-thirds) into `web-apps/hyperframes/sai-bNvMM-trim-review/`. Auto-called at end of `--prep`.
4. **render phase** — `orchestrate --render`: read SEGMENTS.json → per-segment ProRes reels (port `_cut_preview.py`) → H.264 angles → export + `_INFO.txt`. Reuse `cut.py`'s ProRes extract/concat where possible.
5. **docs** — README + CLAUDE.md (batch-pipeline) + memory `workflow_sai_batch3_2cam_qa.md` updated to point at the integrated commands; note select.py is now a seed only.

## Don'ts
- Don't delete select.py — demote to seed proposal.
- Don't change the deliverable convention (ANGLES/ H.264 + ProRes masters in Cut/).
- Don't touch the .env root (already fixed to D:/Sai).
- Keep all existing tests green; add new ones per task.
