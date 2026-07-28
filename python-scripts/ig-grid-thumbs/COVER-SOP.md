# IG Grid Cover SOP — Sai

Rules for making Instagram profile-grid thumbnail covers. Follow these on every
cover. Tool: `render_thumb.py` (+ `grid_preview.py`). Brand source of truth:
`business/sai-karra/editor-onboarding/03-brand-template-spec.md`.

## Photo
1. Use the ORIGINAL photo — no cropping, zooming, blur bars, or AI-editing the
   image itself, unless Gray specifically asks.
2. Never use a frame with eyes closed or head thrown back. Pick a clean,
   engaged frame (mid-smile / gesturing / looking at lens).
3. Prefer intriguing / dynamic shots over static ones (subway coffee shot beat
   the beanbag shot).
4. Show two people when the video is an interview (Sai + Hamza, Sai + Josh).
5. Source photos ONLY from the SSD footage (`/Volumes/Footage/Sai/...`). NEVER
   scrape Instagram — shadow-ban risk. Finished shorts live in
   `03_DELIVERED/shorts/`; raw clips in `01_ORGANIZED/` and `05_FOOTAGE_LIBRARY/`.

## Face
6. His whole face / head must be visible.
7. Title stays CENTERED — unless centered would cover his face, then move it
   down (or up) just enough to clear the face. Never cover the face.
8. A face turned away from camera is fine (e.g. "why I moved to NYC").

## Built-in video captions & graphics
9. No burned-in captions or graphics from the video may show on the cover —
   only the title caption.
10. Preferred removal = position the title label to COVER the built-in text.
    Not blur, not AI-erase, unless Gray asks. (Built-in captions are often 2-3
    lines and taller than the 2-line label — nudge --y until fully covered.)

## Title text
11. Hook psychology, like a YouTube thumbnail — open loops that make people want
    the answer. Not plain topic summaries.
12. Short: 3-5 words ideal, 7 words hard max.
13. Must match what's actually said in the video (transcript-verified via
    mlx-whisper; ~10s/video).
14. NO punctuation (no periods/commas). The "$" symbol is OK.

## Style
15. Solid black label, full opacity, rounded, hugging each line (`--bg pill`).
16. Montserrat ExtraBold, white text.
17. Accent word(s) in Trendify orange #F28129 — ~90/10 ratio. One word usually,
    up to two when there are genuinely two power words. Blue is an option.
18. Names/acronyms stay capitalized: Sai, Stanford, NYC, MIA, ATX, CEO, CMO,
    ROI, AI, Trendify (see CAP dict in render_thumb.py).

## Output & workflow
19. Export as 1080x1920 JPEGs, numbered in grid order, named by title, into an
    `EXPORT-JPEG/` folder.
20. Build an HTML review page pairing each cover with its video transcript so
    Gray can verify titles (see REVIEW-*.html examples).
21. Applying covers is manual on Gray's side: IG app -> reel -> Edit -> Change
    cover -> pick from camera roll. IG can't change covers on already-posted
    reels via any tool; future posts ship the cover in the posting package.

## render_thumb.py flags
- `--frame IMG` or `--video VID --time SEC` — source
- `--title "line1\nline2"` — use \n for line breaks
- `--accent "word1,word2"` — comma-separated; matched after stripping punctuation
- `--pos top|center|bottom` — vertical anchor (default top)
- `--y 0.0-1.0` — explicit title-block top as fraction of height (overrides pos;
  use to cover built-in captions precisely)
- `--cx 0.0-1.0` — horizontal crop focus
- `--bg pill|scrim|none` — label background (pill = the locked style)
