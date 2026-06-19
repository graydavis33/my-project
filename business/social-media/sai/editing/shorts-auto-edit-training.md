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

### B3 V3 — "Shedding the Old Me" (C2742 / MVI_5044, 2026-06-19) — trim went notably better than V2
Built directly with the multicam pipeline (full sources → sync → mlx transcribe → word-level cut). Gray: *"better work at trimming than batch 3 video 2."* The iterations were about **clipping** and **stutters**, not which lines to keep. New lessons:
- **Don't chop where Sai didn't pause.** When he stutters/self-corrects mid-sentence with NO silence ("interact with people, *that I couldn't expect to give other people,* that I couldn't give other people love…"; "anger *with just things, with just, with just,* with self-belief and self-love"), a clean cut there CLIPS the word. Fix = keep the **whole continuous take** (set `PAUSE_S` high so a segment isn't auto-split), accepting the small natural stumble. Clipping is worse than a stutter.
- **TAIL must be ~0.30, not 0.05–0.10.** Whisper marks word-*ends* early, so the old "kill the air → 0.05–0.10 tail" clips trailing words ("people"@22s, "anger"@36s both clipped at 0.0–0.06 tail). REFINED master rule: collapse genuine **held silence between/within** lines, but give each kept word **~0.25–0.30s tail** so it rings. "Kill the air" = remove dead pauses, NOT shave a word's natural decay.
- **Heed Sai's own cut cues.** He ended with "…I am exactly where I'm supposed to be" then said *"Actually, last part cut out. I think we're good"* — i.e. cut that line. Ending on it felt unresolved. End where content resolves ("…with self-belief and self-love").
- **Unsalvageable stutter → ask Gray.** Offered keep-clean-but-clipped / keep-natural-delivery / splice. **Gray chose KEEP NATURAL DELIVERY** for the closer.
- **AUDIO RULE:** finals use the **LAV-MIC camera's audio only** — which camera that is VARIES per shoot (one cam carries the lav, the other only the room mic). Confirm/detect per video (lav = cleaner/closer/louder, less reverb). Vid 1–3 = B-cam, but don't assume. (Both the old "B-cam only always" and the older A-answer/B-question blend are deprecated.)
- **B-roll standard (Gray, 2026-06-19):** **5 horizontal videos per talking point**, no photos, no vertical; primary source = the "B-roll Ep 2" shoot (`Sai/B-roll 06:17:26`) + the horizontal footage library.

### Earlier batches (carried forward)
- Fortune 500 B2V8 etc.: ~41% tightening, dead-air collapsed (became
  `D:/Sai/01_ORGANIZED/Batch 2/_b2_edit/trim_silence.py`, collapses gaps
  ≥0.30s), aborted-then-restated takes dropped, leading filler conjunctions
  trimmed in LIST formats. Consistent with the master rule above.

## Status
Editing the rest of Batch 3 is **gated** on Gray finishing the footage-organizer
batch-filtering setup. Until then: bank data points, don't auto-edit the batch.
