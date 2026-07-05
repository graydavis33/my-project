# Quote Cards — Animated (2026-07-05)

Animated version of the dark-navy quote graphics (first one: Sharran Srivatsaa
"Goodwill is worth 100X"). The card keeps its ORIGINAL graphic size (1206x460)
centered on a 1920x1080 canvas, with chroma green (#00FF00) around it.

## Animation
1. Card background fades in (0.9s)
2. Quote words fade in one-by-one, left to right in reading order
   (soft slide + unblur, 0.07s stagger)
3. Attribution rises in after the quote finishes
4. Holds to the end (8s total) — fade out in Premiere if needed

## Two output flavors per graphic
- **Green-screen MP4** (default render) — key out in Premiere. CAVEAT: during
  the ~1s fade-in the card is semi-transparent over green, so the keyed card
  can look green-tinted while fading. Fine if the fade happens over busy
  footage; if it bugs Gray, use the alpha version.
- **Transparent ProRes 4444 .mov** — true alpha, clean fade, drops straight
  into Premiere. Bigger file (~100MB per 8s). Pipeline: render WebM with
  `canvasBg: "transparent"`, convert with ffmpeg.

## Making the NEXT graphic (no code changes needed)
```bash
cd ~/Desktop/my-project/web-apps/hyperframes/quote-cards-2026-07-05

# Green-screen MP4
npx --yes hyperframes@0.6.51 render --fps 60 --variables '{
  "quote": "“New quote text here.”",
  "attribution": "– Author Name"
}'

# Transparent ProRes (render WebM, then convert)
npx --yes hyperframes@0.6.51 render --fps 60 --format webm --variables '{
  "quote": "“New quote text here.”",
  "attribution": "– Author Name",
  "canvasBg": "transparent"
}'
ffmpeg -c:v libvpx-vp9 -i renders/<the.webm> -c:v prores_ks -profile:v 4444 \
  -pix_fmt yuva444p10le -vendor apl0 renders/Quote-Card-<Name>_ALPHA.mov
```

Notes:
- Include the curly quote marks “ ” in the quote string (matches the source graphics).
- Attribution uses an en dash: `– Name`.
- Longer quotes: drop `quoteSize` (default 46) or bump `cardHeight` via `--variables`.
- Output lands in `renders/`. 1920x1080 canvas, 60fps, 8s.

## Variables (defaults)
- canvasBg `#00FF00` (string; use `transparent` for alpha renders)
- bgColor `#232B3B` · textColor `#FFFFFF`
- cardWidth 1206 · cardHeight 460 · cornerRadius 14
- quoteSize 46 · attrSize 38
- bgFade 0.9 · wordsStart 0.8 · wordStagger 0.07 · wordDuration 0.6

## Delivery
Renders are build artifacts (gitignored). Copy the final file wherever the
graphic is being used (Footage SSD per the usual Sai-VFX convention, or
directly into the edit).
