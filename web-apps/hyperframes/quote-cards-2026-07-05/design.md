# Quote Cards — Animated (2026-07-05)

Animated version of the dark-navy quote graphics (first one: Sharran Srivatsaa
"Goodwill is worth 100X"). Look matches the source image: dark navy background,
bold white text, centered, attribution line below.

## Animation
1. Background fades in (0.9s)
2. Quote words fade in one-by-one, left to right in reading order
   (soft slide + unblur, 0.07s stagger)
3. Attribution rises in after the quote finishes
4. Holds to the end (8s total) — fade out in Premiere if needed

## Making the NEXT graphic (no code changes needed)
The quote and attribution are composition variables. Render a new card with:

```bash
cd ~/Desktop/my-project/web-apps/hyperframes/quote-cards-2026-07-05
npx --yes hyperframes@0.6.51 render --fps 60 --variables '{
  "quote": "“New quote text here.”",
  "attribution": "– Author Name"
}'
```

Notes:
- Include the curly quote marks “ ” in the quote string (matches the source graphics).
- Attribution uses an en dash: `– Name`.
- Longer quotes: drop `quoteSize` (default 68) via the same `--variables` JSON.
- Output lands in `renders/`. 1920x1080, 60fps, 8s.

## Variables (defaults)
- bgColor `#232B3B` · textColor `#FFFFFF`
- quoteSize 68 · attrSize 46 · maxTextWidth 1560
- bgFade 0.9 · wordsStart 0.8 · wordStagger 0.07 · wordDuration 0.6

## Delivery
Renders are build artifacts (gitignored). Copy the final MP4 wherever the
graphic is being used (Footage SSD per the usual Sai-VFX convention, or
directly into the edit).
