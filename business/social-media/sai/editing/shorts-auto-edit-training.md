# Sai Shorts — Auto-Edit Training Log

Living training log for the HyperFrames shorts auto-editor (trim/sync only — no
B-roll, music, or captions; that's Gray's job in Premiere). Gray hand-trims the
auto-edit's output, posts the final, then Claude diffs his final against the
auto-pick. Each batch video = another data point. **Goal: shrink Gray's manual
trimming over time by teaching the auto-editor his pacing.**

## How the auto-editor works
- Per-video tool: `web-apps/hyperframes/sai-b3v{N}-trim-review/build_review.py`.
- A hand-listed `SEGMENTS` table (src proxy, source-in, source-out, read-along
  text, tag, head-pad, tail-pad) → `segments.json` + `index.html` review page.
- Review is a **B-cam 720p proxy**; the final render uses **A-cam Rode audio for
  the answer + B-cam audio for the question** (this is why finals are landscape).
- **The tuning lever:** `HEAD, TAIL = 0.10, 0.25` at the top of `build_review.py`
  — the seconds of padding added to every clip's head/tail.

## Master rule (so far): KEEP THE SELECTION, KILL THE AIR
The auto-editor's *selection* (which lines, what order) has been right. The gap
is purely **pacing** — it leaves too much silence on the tails.
- Drop `TAIL` from **0.25 → ~0.05–0.10**. Keep `HEAD ~0.10`.
- When a line ends and Sai breathes/pauses before the next thought, cut straight
  to the next line — don't hold the pause (tighten that clip's source-out).
- Target ~0.1–0.2s of breath between sentences, no held dead air.
- Strip leading "And/So/But" **only in list/enumeration formats**, NOT in a
  flowing argument (there they're connective tissue — keep them).

## Data points

### B3 V1 — "Business is Spiritual" (final 2026-06-17)
- Auto-edit: 8 segments, ~34.9s, B-cam, landscape. (Batch 3 verbal hook #2,
  "The Contrarian Belief.")
- Gray's final: **26.69s → ~24% tighter.**
- **Selection perfect** — kept all 8 segments, same order, same content. No
  cuts, adds, or reorders.
- Whole delta = tail-trimming. Biggest cuts were the two clips with a pause
  before the pickup: seg5 "opportunities find you" −2.2s, seg6 "universe/orbit"
  −1.4s. Small ~0.3–0.7s tail trims on the rest.
- Gray KEPT the leading "And…/So…" on segs 4/7/8 (flowing argument).

### Earlier batches (carried forward)
- Fortune 500 B2V8 etc.: ~41% tightening, dead-air collapsed (became
  `D:/Sai/01_ORGANIZED/Batch 2/_b2_edit/trim_silence.py`, collapses gaps
  ≥0.30s), aborted-then-restated takes dropped, leading filler conjunctions
  trimmed in LIST formats. Consistent with the master rule above.

## Status
Editing the rest of Batch 3 is **gated** on Gray finishing the footage-organizer
batch-filtering setup. Until then: bank data points, don't auto-edit the batch.
