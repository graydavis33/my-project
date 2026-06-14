# Sai Batch 2 Vid 3 — Competing Through Intuition — Graphics Package

Source: **Vid 3 "Competing Through Intuition"** (Batch 2). Same locked Sai HyperFrames
brand style as Vid 8 (`sai-b2v8-fortune500/`), Vid 5, Vid 9, Vid 7, Vid 4.

Core theme: **small/nimble businesses beat big ones through intuition + creativity, while
big companies kill that edge with bureaucracy.** Steel/corporate = heavy, rule-bound, stiff.
Orange-glass = Sai's nimble, glowing, intuitive advantage.

## Final spoken content (from the cut transcript / script)
- Compete with the biggest businesses → you need to use your **intuition**
- Big companies = a lot of **bureaucracy. Rules. Regulations.** → limits creativity + intuition
- **That's exactly where your advantage lies**
- Look at the landscape → **see what's missing that you could uniquely provide** (out of the box / creative)
- Implement it → sign a couple clients
- Everyone else gets bigger + adds more bureaucracy → **you do the opposite: get huge but still allow intuition + creativity**
- **Trust yourself.** Trust the universe will give you ideas when most needed. Listen to the
  voice that's hard to explain.

## Script beats → infographics (all 4 selected by Gray)
- "see what's missing you could uniquely provide" → **ig-1-find-the-gap**
- "get huge but still allow for intuition" (vs everyone else stiffening) → **ig-2-grow-stay-nimble** (HERO / flagship candidate)
- "bureaucracy / rules / regulations limit creativity" → **ig-3-bureaucracy-vs-intuition**
- "trust the universe will give you ideas / the voice hard to explain" → **ig-4-trust-the-signal**

> ⭐ **FLAGSHIP TARGET: `ig-2-grow-stay-nimble/`.** In the league of the b2v5 airplane-runway
> (the starred benchmark): two towers rise through space + a synced 3D camera push-in. The grey
> corporate tower accretes red-tape layers + locks and stiffens; Sai's orange-glass tower grows
> just as tall but stays glowing/fluid with intuition sparks. See memory
> `feedback_prefers_3d_motion_graphics.md`.

## Format
- 1080×1920 vertical. Beat cards 24fps; the flagship (`ig-2`) renders at **60fps** for the
  camera move.
- **Transparent background** (orange-glass glow + soft drop shadows → render ProRes 4444
  alpha `.mov`; no chroma-key).
- Standalone composition per folder (no `<template>`), `data-composition-id="main"`, one
  preview port each. Single scene → entrance + idle motion, **NO exit animations** (the
  Premiere cut ends the card).

## Colors (locked)
- **Trendify orange** `#F28129` — primary emphasis, Sai's nimble advantage, payoff
- Glass gradient `#FFC68A → #F28129 → #D66416`, `2px solid #fff` border, inset highlights +
  `0 0 24px rgba(242,129,41,0.55)` glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow
- **Steel/dim glass** `#8A93A0 → #5C6470 → #3C424C` — the BIG bureaucratic companies (heavy,
  desaturated, corporate)
- **Red tape** `#C8443A` / `rgba(200,68,58,0.85)` — bureaucracy: rules, regulations, locks
- **White** `#FFFFFF` — text, figures, badges

## Typography
- **Montserrat** — Black (900) hero, ExtraBold (800) labels, UPPERCASE, letter-spacing
  −0.01 to −0.02em. `tabular-nums` on numbers.
- Drop shadows `0 4px 14px rgba(0,0,0,0.45)`; one line per `<div>` (no `<br>` mid-line).

## Motion
- Entrance stagger ~0.18–0.26s, first offset 0.10–0.15s. Vary eases (≥3 per card).
- **Flagship camera rule (from the airplane):** pan (X) + zoom (Y + scale) move TOGETHER in
  ONE synced ease (`power2.inOut`) so the framed target glides straight to center — never lead
  the pan ahead of the zoom (overshoot/swing-back). `transform-origin: 0 0`; to frame world
  point P at scale s, `tx = 540 − s·Px`, `ty = 960 − s·Py`.
- Stepped/looping motion uses finite `repeat` counts (never `repeat: -1`), seekable + time-based.
- `fromTo` tweens with a visible from-opacity need `immediateRender:false` so rings/strokes
  don't flash on frame 0.
- No `Math.random()`/`Date.now()` — seeded mulberry32 if pseudo-random needed.

## Note on "fewer words"
Let the visual carry the story — steel-vs-orange, the gap in the skyline, the red tape. Keep
text to a single short label/kicker per card; on-card text competes with burned-in captions
([[feedback_infographics_fewer_words]]).

## Render
- All alpha ProRes 4444 (`render --format mov`). Export to
  `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 3 - Competing Through Intuition/`.
- Preview each + get Gray's OK BEFORE rendering (locked rule).
