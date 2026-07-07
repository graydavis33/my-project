# Logos Mosaic Row — DESIGN

B-roll asset: three app logos (Slack / Notion / Scribe) rise into a row on a green screen,
one by one, mosaic-pixelated so you can tell each is *a logo* but not exactly which one.
Meant to be chroma-keyed and floated over Gray's talking-head footage in a Sai short.

## Style Prompt
Flat, clean, chroma-key deliverable. No decoration, no text, no gradients — the frame is
solid chroma green and the only content is the three pixelated logo marks in a centered
horizontal row. The pixelation IS the aesthetic: coarse-enough mosaic that identity is
obscured but the "it's a logo" read survives.

## Colors
- `#00B140` — chroma key green (full-frame background; the ONLY background)
- Logo marks keep their own baked colors (Slack multicolor, Notion black cube, Scribe badge)

## Typography
- None. This composition has no text.

## Motion
- Each logo eases in from below (`y: 150 → 0`) with `opacity: 0 → 1`
- `ease: power3.out`, `duration: 0.9s` — smooth deceleration into place
- One-by-one via `stagger: 0.35s` (left → right)
- Hold on the full row after entrance (no exit — it's a loopable B-roll hold)

## Mosaic Spec
- Source: transparent high-res icon → square-fit → downscale to **16px** (BILINEAR) → display
  at 320px with `image-rendering: pixelated` (= ~20px hard blocks)
- 16px is the tuned "middle": at 20px+ the Notion N / Scribe S read too clearly; at 14px the
  shapes start to mush. Bump to 14 for blurrier, 18 for sharper.

## What NOT to Do
- No text, labels, or captions
- No non-green background, no vignette, no drop shadows (would fringe the key)
- No smooth gaussian blur — the look is blocky mosaic, not soft blur
- No exit animation / fade-out — hold the row
- Don't animate the same logo's y/opacity from two tweens
