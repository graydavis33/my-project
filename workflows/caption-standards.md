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

- Snappy per-phrase pop-in: `scale 0.92 → 1` + fade, `duration 0.13`,
  `ease back.out(1.6)`, synced to the spoken phrase (group `start` = first word's
  start). Replace, don't overlap.

## Workflow

1. Transcribe with **Whisper large-v3** word-level on the RTX 5070
   (`web-apps/<project>/transcribe.py` pattern → `words.json`). English audio.
2. `build.py` groups words (≈3/line, breaks on sentence end + pauses ≥0.30s),
   applies the case + punctuation rules above, and bakes `GROUPS` into a
   HyperFrames composition (deterministic — no runtime grouping).
3. `lint` + `validate` + `inspect` clean → preview for Gray → render at the
   source's fps → deliver.

Reference implementation: `web-apps/sai-b01v06-captions/`.

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
