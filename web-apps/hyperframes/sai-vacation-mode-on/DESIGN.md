# Sai HyperFrames — VACATION MODE: ON

Single-scene infographic. Stripped to two elements: a "VACATION MODE" wordmark and a
sleek toggle switch. The knob snaps left→right across an orange-glass track that ignites,
the power glyph lights orange, and the track label flips OFF→ON. Modern, minimal, punchy —
"turning on vacation mode." Same locked Sai HyperFrames brand as Vid 7/10.

## Format
- 1080×1920 vertical, 24fps
- **Transparent background** → render ProRes 4444 alpha `.mov` (glow + soft drop shadows).
  Composites over Sai footage in Premiere.
- Standalone composition (no `<template>`), one preview port.

## Beats (single continuous scene, ~3.4s)
1. "VACATION MODE" wordmark drops in (white / orange).
2. Toggle appears in its OFF state (muted track), knob pops in on the LEFT, OFF label.
3. Tiny anticipation pull-back, then the knob SNAPS left→right: the track ignites to
   orange-glass, a glow blooms behind it, the power glyph lights orange.
4. Track label flips OFF→ON. Final frame holds.

## Colors (locked)
- Trendify orange `#F28129` — ON track, glow, ON badge, sun, power glyph (lit)
- White `#FFFFFF` — wordmark, knob, badge text, sun core
- ON track gradient `#FFA858 → #F28129 → #D66416`; OFF track `rgba(54,46,38,0.55)`
- Orange-glass recipe: linear orange gradient, `2px solid #fff` border, inset highlights +
  `0 0 24px rgba(242,129,41,0.55)` glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow.

## Typography
- **Montserrat** — Black (900) wordmark + ON badge, ExtraBold (800) sub, UPPERCASE
- Wordmark ~120px (two lines), badge ~84px, sub ~36px

## Motion
- Knob slide on `back.out` for the satisfying snap; track/glow/badge crossfade on flip
- Sun rays burst (`back.out(2)`) then slow finite rotation; everything seekable
- Single scene → NO scene-exit animation (Premiere cut ends it; final frame holds)
- All time-based / seekable, finite repeats only — no `repeat:-1`, no `Math.random()`/`Date.now()`

## What NOT to do
- No emojis — drawn SVG only (locked rule)
- No system fonts / `#333` / `#3b82f6` — Montserrat + brand palette only
- No `<br>` mid-line — one div per text line
- No infinite repeats, no non-deterministic values

## Workflow
Preview in the studio and get Gray's OK BEFORE rendering (locked rule). Then render
ProRes 4444 alpha `.mov` → copy to `D:/Sai/06_ASSETS/Visual Effects/`.
