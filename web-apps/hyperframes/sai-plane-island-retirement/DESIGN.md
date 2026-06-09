# Sai HyperFrames — Plane → Island (Retirement / Vacation)

Single-scene drawn infographic. A plane flies in from the left to center, banks/turns,
climbs off the top-right out of frame, then descends and parks on a tropical island —
the destination. Metaphor: the flight = the working journey, the island = the payoff.
Retirement as the forever vacation. Same locked Sai HyperFrames brand as Vid 7/10.

## Format
- 1080×1920 vertical, 24fps
- **Transparent background** → render ProRes 4444 alpha `.mov` (glow + soft drop shadows,
  so alpha not chroma-key). Composites over Sai footage in Premiere.
- Standalone composition (no `<template>`), one preview port.

## Beats (single continuous scene, ~6.2s)
1. Plane enters from left, flies a gentle arc to center; a dotted orange flight-path
   trails behind it (the journey).
2. Plane banks/turns at center and climbs off the top-right, fading at the frame edge.
3. Island reveals in the lower third — sun, sandy mound, palm tree, orange/white beach
   umbrella.
4. Plane descends back into frame and parks on the island (it arrived).
5. Orange-glass label lands: kicker DESTINATION · hero RETIREMENT · sub "the forever vacation".

## Colors (locked)
- Trendify orange `#F28129` — plane accents, trail dots, island sand, glass label
- White `#FFFFFF` — plane body, palm fronds, umbrella stripes, label text
- Warm gradients: sand `#FFC98A → #F28129 → #D8691A`, label glass `#F0871F → #C9560F`
- Sun gold `#FFC76B`
- Orange-glass recipe on the label: linear orange gradient, `2px solid #fff` border,
  inset highlights + `0 0 24px rgba(242,129,41,0.55)` glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow.

## Typography
- **Montserrat** — Black (900) hero word, ExtraBold (800) kicker/sub, UPPERCASE hero/kicker
- Hero ~96px, kicker ~30px tracked, sub ~40px

## Motion
- Plane path driven by sequential x/y/rotation tweens (seekable); bank emphasised at center
- Island elements pop in (back.out), palm grows from base + subtle sway, sun gentle pulse
- All time-based / seekable, finite repeats only — NO `repeat:-1`, no `Math.random()`/`Date.now()`
- Single scene → NO scene-exit animation (the Premiere cut ends it; final frame holds).
  The plane's mid-flight fade-out as it leaves frame is choreography, not a scene exit.

## What NOT to do
- No emojis — drawn SVG only (locked rule)
- No system fonts / `#333` / `#3b82f6` — Montserrat + brand palette only
- No `<br>` mid-line — one div per text line
- No infinite repeats, no non-deterministic values

## Workflow
Preview in the studio and get Gray's OK BEFORE rendering (locked rule). Then render
ProRes 4444 alpha `.mov` → copy to `D:/Sai/06_ASSETS/Visual Effects/`.
