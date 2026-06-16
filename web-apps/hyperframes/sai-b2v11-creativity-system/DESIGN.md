# Sai Batch 2 Vid 11 — Turn Your Creativity Into a System — Graphics Package

Source: **Vid 11 "Turn Your Creativity Into a System"** (Batch 2). Same locked Sai HyperFrames
brand style as Vid 6 (`sai-b2v6-onboarding/`), Vid 3, Vid 8, Vid 5, Vid 9, Vid 7, Vid 4.

Core theme: **creativity is worthless until you systemize it.** Chaos / scattered sparks = raw
creativity. Orange-glass order = the system that makes every idea land.

## Final spoken content (from the cut script)
- **You win by turning your creativity into a system.**
- Creativity means nothing unless you systemize it; structure means nothing without creativity.
- The most tactical way to add structure: **set aside time every week for planning.**
- While everyone's obsessed with execution / go-go-go, spend just as much time **planning.**
- Set a cadence — once or twice a week. **Clear your calendar. Show up with a pen and paper.**
- Write down all your creative ideas, plan how to attack them.
- **Creativity without structure = one-hit wonder. Structure without creativity = like everyone else.**
- **We've produced close to 10,000 ads. Without structure, only 5 would be creative. With a
  system, every single one gets to be creative.**

## Script beats → infographics
- "turn your creativity into a system" (hook/core) → **ig-1-creativity-funnel** (chaos→order)
- "creativity without structure = one-hit wonder / structure without creativity = like everyone
  else" → **ig-2-equation** (two failure states vs the merged win)
- "set aside time every week… clear your calendar… pen and paper" → **ig-3-weekly-planning**
- "10,000 ads — only 5 creative without a system, ALL creative with one" → **ig-4-ten-thousand-ads** (HERO)

> **STYLE RULE (locked, from the b2v5 airplane / b2v3 rocket bar):** premium = a clean recognizable
> ICON on a high-contrast dark "stage" card + crisp white marks + soft drop shadows + ONE clear
> motion + a camera payoff, with heavy restraint — NOT texture. No graph-paper/ruler grids, no
> busy multi-element diagrams, no on-card label clutter.

## Format
- 1080×1920 vertical. Hero (ig-4) and any camera-push card → 60fps; simpler cards → 24fps.
- **Transparent background** → render **ProRes 4444 alpha `.mov`** (orange glow + soft shadows;
  no chroma-key). Standalone composition per folder (no `<template>`), `data-composition-id="main"`,
  one preview port each. Single scene → entrance + idle + camera move, **NO scene-exit fades**
  (the Premiere cut ends the card).

## Colors (locked)
- **Trendify orange** `#F28129` — the system, the payoff, the creative spark that lands. Glass
  gradient `#FFC68A → #F28129 → #D66416`, `2px solid #fff` border, `0 0 24px rgba(242,129,41,0.55)`
  glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow.
- **Dark stage** `#34302C → #272320 → #1C1916`.
- **White** `#FFFFFF` — figures, marks, neutral tiles.
- **Grey/clutter** `#8A93A0 → #5C6470` — raw/unsystemized, the "like everyone else" dead state.

## Typography
- **Montserrat** — Black (900) hero numbers, ExtraBold (800) labels, UPPERCASE, letter-spacing
  −0.01 to −0.02em, `tabular-nums` on numbers. Drop shadow `0 4px 14px rgba(0,0,0,0.45)`.

## Motion
- Entrance stagger ~0.18–0.26s, first offset 0.10–0.15s. Vary eases (≥3 per card).
- **Camera rule (from the airplane):** pan (X) + zoom (scale) move TOGETHER in ONE synced ease
  (`power2.inOut`). `transform-origin: 0 0`; to frame world point P at scale s, `tx = 540 − s·Px`,
  `ty = 960 − s·Py`.
- Finite `repeat` counts only (never `repeat: -1`); seekable + time-based.
- `fromTo` tweens with a visible from-opacity need `immediateRender:false`.
- No `Math.random()`/`Date.now()` — seeded mulberry32 if needed.

## Note on "fewer words"
Let the visual carry it. One short label/number per card; on-card text competes with burned-in
captions.
