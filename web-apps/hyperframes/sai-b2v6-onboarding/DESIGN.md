# Sai Batch 2 Vid 6 — How to Build a Better Onboarding — Graphics Package

Source: **Vid 6 "How to Build a Better Onboarding"** (Batch 2). Same locked Sai HyperFrames
brand style as Vid 3 (`sai-b2v3-intuition/`), Vid 8, Vid 5, Vid 9, Vid 7, Vid 4.

Core theme: **a messy, complicated onboarding (10+ disorganized pages) becomes simple, ordered,
and owned.** Clutter / grey = the bad first version. Orange-glass = the clean, simplified system.

## Final spoken content (from the cut script)
- First onboarding was awful — **over 10 pages for one simple thing, nothing organized**
- Sat down as a team → 4 steps: review what went wrong → implement changes → reorder
  chronologically → simplify 90%, cut what wasn't needed
- **"We went from 10 pages to 3"**
- **Pro tip: send an onboarding feedback form after every new hire** so you keep improving the system
- **"Better onboarding is just delegation at its finest. Everyone owns their own avenue."**
- The creators we onboarded will crush — they understand exactly what we want

## Script beats → infographics
- "over 10 pages… nothing organized" + **"we went from 10 pages to 3"** → **ig-1-ten-to-three** (HERO)
- "everyone owns their own avenue" (delegation) → **ig-2-own-your-lane**
- "send a feedback form… keep improving the system" → **ig-3-feedback-loop**

> **STYLE RULE (locked, from the b2v5 airplane / b2v3 rocket bar):** premium = a clean recognizable
> ICON on a high-contrast dark "stage" card + crisp white marks + soft drop shadows + ONE clear
> motion + a camera payoff, with heavy restraint — NOT texture. No graph-paper/ruler grids, no
> busy multi-element diagrams, no on-card label clutter. See `feedback_prefers_3d_motion_graphics.md`.

## Format
- 1080×1920 vertical, 24fps (the hero may go 60fps for its camera push).
- **Transparent background** → render **ProRes 4444 alpha `.mov`** (orange glow + soft shadows;
  no chroma-key). Standalone composition per folder (no `<template>`), `data-composition-id="main"`,
  one preview port each. Single scene → entrance + idle + camera move, **NO scene-exit fades**
  (the Premiere cut ends the card).

## Colors (locked)
- **Trendify orange** `#F28129` — the simplified/clean system, the payoff. Glass gradient
  `#FFC68A → #F28129 → #D66416`, `2px solid #fff` border, `0 0 24px rgba(242,129,41,0.55)` glow +
  `0 8px 22px rgba(0,0,0,0.30)` drop shadow.
- **Dark stage** `#34302C → #272320 → #1C1916`.
- **White** `#FFFFFF` — pages, figures, marks. Thin grey content lines `rgba(120,128,140,0.5)`.
- **Grey/clutter** `#8A93A0 → #5C6470` — the messy old version (desaturated).

## Typography
- **Montserrat** — Black (900) hero numbers, ExtraBold (800) labels, UPPERCASE, letter-spacing
  −0.01 to −0.02em, `tabular-nums` on numbers. Drop shadow `0 4px 14px rgba(0,0,0,0.45)`.

## Motion
- Entrance stagger ~0.18–0.26s, first offset 0.10–0.15s. Vary eases (≥3 per card).
- **Camera rule (from the airplane):** pan (X) + zoom (Y + scale) move TOGETHER in ONE synced
  ease (`power2.inOut`) so the framed target glides straight to center — never lead the pan ahead
  of the zoom. `transform-origin: 0 0`; to frame world point P at scale s, `tx = 540 − s·Px`,
  `ty = 960 − s·Py`.
- Finite `repeat` counts only (never `repeat: -1`); seekable + time-based.
- `fromTo` tweens with a visible from-opacity need `immediateRender:false`.
- No `Math.random()`/`Date.now()` — seeded mulberry32 if needed.

## Note on "fewer words"
Let the visual carry it (the pile shrinking, the lanes, the loop). One short label/number per card;
on-card text competes with burned-in captions ([[feedback_infographics_fewer_words]]).

## Render
- All alpha ProRes 4444 (`render --format mov`). Export to
  `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 6 - How to Build a Better Onboarding/`.
- **Preview each + get Gray's OK BEFORE rendering** (locked rule).
