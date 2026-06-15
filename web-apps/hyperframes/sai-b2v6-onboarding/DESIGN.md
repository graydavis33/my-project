# Sai Batch 2 Vid 6 — How to Build a Better Onboarding — Graphics Package

Source: **Batch 2 Vid 6 "How to Build a Better Onboarding"** (1080×1920, ~75s).
Same locked Sai HyperFrames brand style as Vid 3 (`sai-b2v3-intuition/`), Vid 8, Vid 5,
Vid 9, Vid 7, Vid 4.

Core theme: **a broken, bloated onboarding (10+ messy pages, disorganized) rebuilt into a
clean, simple system (3 pages, 4 ordered steps).** Messy/grey = the old broken process.
Orange = the fixed, simplified, intentional system.

## The premium bar (read before touching anything)
The b2v3 v1 comps were REJECTED ("look cheap/flat"). Root cause: textured CSS rectangles +
dense graph-paper window grids read like a ruler, not architecture.

**Premium = a clean recognizable ICON on a high-contrast dark "stage" card + crisp white
marks + soft drop shadows + ONE clear motion + a camera payoff + heavy restraint.**
NOT texture, NOT grids, NOT flat textured rectangles, NOT busy multi-element diagrams,
NOT on-card label clutter. The visual carries the story; text is one short kicker/payoff.

## Script beats → infographics (the 2 strongest)
- **"We went from 10 pages to 3 / simplify 90%"** → **ig-1-ten-to-three** — a messy tall
  leaning stack of pages on a dark stage card collapses into a clean, squared 3-page stack
  with an orange ✓. The single most visual, quotable line in the script.
- **"Here's the exact framework / step 1–4"** → **ig-2-the-framework** — four clean numbered
  step-tiles build up in order on a dark stage card (the onboarding *system*), connector
  line draws between them, camera frames the finished system.

## Format
- 1080×1920 vertical. **60fps** (project default — Gray speed-ramps in Premiere).
- **Transparent background** — soft drop shadows + orange glow → render ProRes 4444 alpha
  `.mov` (yuva444). No chroma-key (soft shadows fringe on green).
- Standalone composition per folder (no `<template>`), `data-composition-id="main"`, one
  preview port each. Single scene → entrance + ONE motion + camera payoff. **NO exit
  animations** (the Premiere cut ends the card).

## Max-agency variable parameterization (REQUIRED)
Every meaningful value exposed as a HyperFrames variable on the `<html>` root via
single-quote-wrapped JSON on ONE line (`data-composition-variables='[...]'`), read in-script
with `window.__hyperframes.getVariables()` with hardcoded fallbacks. Minimum: `orange`,
`white`, `strokeWidth`, `cornerRadius`, each key timing, text strings, counts.

## Colors (locked)
- **Trendify orange** `#F28129` — the fixed/simplified system, payoff, accent
- Orange gradient `#FFC68A → #F28129 → #C8631A`, `#fff` border, soft glow
  `0 0 24px rgba(242,129,41,0.55)` + drop shadow `0 8px 22px rgba(0,0,0,0.30)`
- **Dark stage card** `#34302C → #272320 → #1C1916` — the high-contrast stage every icon
  sits on, `inset 0 2px 5px rgba(255,255,255,0.08), 0 16px 38px rgba(0,0,0,0.46)`
- **Steel/dim grey** `#8A93A0 → #5C6470 → #3C424C` — the OLD broken / cluttered process
- **White** `#FFFFFF` — text, page sheets, crisp marks, thin strokes (1.5–2px)

## Typography
- **Montserrat** — Black (900) hero kicker, ExtraBold (800) labels/numbers, UPPERCASE,
  letter-spacing −0.01 to −0.02em, `tabular-nums` on numbers.
- Drop shadows `0 4px 14px rgba(0,0,0,0.45)`; one line per `<div>` (no mid-line `<br>`).

## Motion
- Entrance stagger ~0.18–0.26s, first offset 0.10–0.15s. Vary eases (≥3 per card).
- **Camera rule (from the airplane flagship):** pan (X) + zoom (Y + scale) move TOGETHER in
  ONE synced ease (`power2.inOut`) so the framed target glides straight to center — never
  lead the pan ahead of the zoom. `transform-origin: 0 0`; to frame world point P at scale
  s: `tx = 540 − s·Px`, `ty = 960 − s·Py`.
- `fromTo` with a visible from-opacity → `immediateRender:false` (no frame-0 flash).
- No `Math.random()`/`Date.now()` — seeded mulberry32 if pseudo-random needed.
- `data-layout-allow-overflow` on layers with elements that start off-canvas.

## Render
- All alpha ProRes 4444 (`npm run render` → `--fps 60`; `render --format mov` for alpha).
- Export to `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 6 - How to Build a Better Onboarding/`.
- Preview each + get Gray's OK BEFORE final render (locked rule).
