# Caption Standards (Graydient / Sai)

The house rules for burned-in captions on any short. Apply these every time captions
are built — no exceptions unless Gray overrides for a specific video.

---

## Font

- **Montserrat SemiBold** (font-weight **600**). This is the brand caption font.
- Do NOT use ExtraBold/800 or any other weight unless Gray asks for a one-off.

## Case

- **All lowercase**, EXCEPT the pronoun **"I"** and its contractions: **I, I'm, I've, I'd, I'll**.
- `me`, `my`, `mine`, `myself`, and every other word stay **lowercase**.
  - ✅ `my only goal` · `straight I showed up` · `I've been there`
  - ❌ `My Only Goal` · `Me` · `My 7th grade`
- **Proper nouns (names) stay capitalized** — e.g. `coach Waddell`, `New York`.
  Keep a per-project proper-noun list in `build.py` (`PROPER_NOUNS`).

## Punctuation

- **None.** Strip periods, commas, question marks, exclamation points, colons,
  semicolons, and quotes.
- **Keep** intra-word apostrophes (I've, didn't, don't) and hyphens in compound
  words (self-belief).

## Layout

- **One line per caption.** Never wrap to two lines. Use short word groups
  (≈3 words) and auto-shrink the font with `window.__hyperframes.fitTextFontSize()`
  so each group fits on a single line.
- **Scaled down** — base ~52px, shrinking as needed (min ~34px). Not huge.
- Portrait (1080×1920): default lower-middle, ~700px from the bottom (`top: ~1180px`),
  centered. Never cover the speaker's face or a top title card.
- **Captions go opposite the graphics.** If the video has burned-in graphics in
  the bottom third (step cards, callouts), put captions in the **top third**
  (`top: ~360px`). Never stack caption text over the editor's graphics.
- One caption group visible at a time; hard `tl.set` kill at each group's end
  (HyperFrames caption exit guarantee).

## Color / Brand

- White text with a strong drop shadow for legibility over video
  (`text-shadow: 0 3px 10px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,0.95)`).
- Brand orange `#F28129` is available for keyword emphasis when Gray asks —
  default is plain white.

## Animation

- **NO flicker at the line change (hard rule — Gray 2026-06-06).** A caption must
  never dim, fade out, slide, or blank in the gap *between* two cards. Those
  inter-card transitions are what read as a "flicker." Keep each card at **full
  opacity, gapless** — it holds until the **next card's start** (last card holds
  to the end), then **hard-cuts** to the next. No fade-out, no crossfade, no
  slide-up entrance, no micro-gap.
- A subtle entrance (pop-in / fade-in) is only acceptable on the **very first**
  card or a card that follows a genuine long pause (it appears over blank, so
  there is nothing to dim against). Within continuous speech, replace instantly.
- For the PIL alpha-layer path (`sai-captions` / `_b2_edit/pipeline.py` /
  `recaption_final.py`): this is enforced by building gapless spans
  (`e = next card start`) and writing each card PNG at full alpha — no
  `alpha_scaled`, no `y_off`, no crossfade. Verify by sampling consecutive
  frames over black: per-frame max luma must stay 255 across every transition
  (a dip to ~200 or a 0 = the flicker is back).

## Workflow

1. Transcribe with **Whisper large-v3** word-level on the RTX 5070
   (`web-apps/<project>/transcribe.py` pattern → `words.json`). English audio.
2. `build.py` groups words (≈3/line, breaks on sentence end + pauses ≥0.30s),
   applies the case + punctuation rules above, and bakes `GROUPS` into a
   HyperFrames composition (deterministic — no runtime grouping).
3. `lint` + `validate` + `inspect` clean → preview for Gray → render at the
   source's fps → deliver.

Reference implementation: `web-apps/sai-b01v06-captions/`.

**Re-captioning a finished cut (SMOOTH no-flicker alpha layer):**
`python python-scripts/sai-captions/recaption_smooth.py "<cut.mp4>" --out "<... - captions.mov>" --preview`
— cross-platform: auto-selects **mlx-whisper large-v3** on Mac / Apple Silicon and
**CUDA openai-whisper** on Windows. Re-transcribes the final cut and renders a ProRes
4444 alpha caption layer + a watchable PREVIEW.mp4, enforcing the no-flicker rule
(fade-in only over blank, hard-cut contiguous cards). Supersedes the old Windows-only
copy at `<footage>/.../Batch 2/_b2_edit/recaption_smooth.py`.

---

## Token Efficiency (applies to the whole video pipeline)

Minimize token usage on every graphics / captions / edit job:

- **Don't re-read files you just wrote or edited** — Edit/Write confirm success; trust them.
- **Don't read full large files** — use Grep/offset reads to grab only the block you need.
- **Batch independent shell calls** into one command; chain lint + render in a single call.
- **Edit, don't rewrite** — change only the lines requested; never paste whole files back.
- **Cheapest verification first** — `lint`; only extract/Read render frames when a render bug is actually suspected, and crop them small.
- **One preview studio at a time** — stop it (TaskStop) when done; don't leave studios running.
- **Keep status replies short** — no recaps of what the user can already see.
- **Reuse existing tooling/patterns** before building new scripts.
