# Sai Batch 2 Vid 8 — Landed a Fortune 500 Client — Graphics Package

Source: **Vid 8 "Landed a Fortune 500 Client"** (Batch 2). Same locked Sai HyperFrames
brand style as Vid 5 (`sai-b2v5-money/`), Vid 9, Vid 7, Vid 4.

> ⭐ **FLAGSHIP TARGET: `ig-3-contract-race/`.** Gray asked for at least one graphic in the
> league of the b2v5 airplane-runway (the starred benchmark) — object moving through space +
> a synced 3D camera pan/zoom, now pushed further with **motion blur** and **perspective depth**.
> Keep it brand-oriented, simple, clean. See memory `feedback_prefers_3d_motion_graphics.md`.

## Final spoken content (from the cut transcript / script)
- Hook: turned down **two $100M mentors** → landed a **Fortune 500 client at age 20**
- Mentors' advice (good advice): you're up against **multi-billion-dollar companies**, the
  sales cycle is too long, don't waste your time
- He **trusted his gut** and went after it anyway
- Competed for the contract against **3 agencies significantly bigger than his** → **WON**
- Lesson: trusting your gut won't always work — but if **1 in 10 bets pays 100x**, it's a
  great bet. Trust your gut regardless.

## Script beats → infographics
- two $100M mentors / advice he turned down → **ig-1-mentors-advice**
- "trust your gut" pivot → **ig-2-trust-gut**
- won the contract vs 3 bigger agencies → **ig-3-contract-race** (HERO / flagship)
- "1 in 10 bets → 100x" → **ig-4-bet-math**

## Format
- 1080×1920 vertical. Beat cards 24fps; the flagship race renders at **60fps** for the
  camera + motion blur (camera-heavy pieces warrant it).
- **Transparent background** (orange-glass glow + soft drop shadows → render ProRes 4444
  alpha `.mov`; no chroma-key).
- Standalone composition per folder (no `<template>`), one preview port each.

## Colors (locked)
- **Trendify orange** `#F28129` — primary emphasis, Sai's marker, payoff
- Glass gradient `#FFC68A → #F28129 → #D66416`, `2px solid #fff` border, inset highlights +
  `0 0 24px rgba(242,129,41,0.55)` glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow
- **Steel/dim glass** `#8A93A0 → #5C6470 → #3C424C` — the BIGGER competitor agencies (heavy,
  desaturated, "corporate")
- **White** `#FFFFFF` — text, figures, badges
- Fail-grey `#4A4F57` + dim — the 9 losing bets (ig-4)

## Typography
- **Montserrat** — Black (900) hero, ExtraBold (800) labels, UPPERCASE, letter-spacing
  −0.01 to −0.02em. `tabular-nums` on numbers.
- Drop shadows `0 4px 14px rgba(0,0,0,0.45)`; one line per `<div>` (no `<br>` mid-line).

## Motion
- Entrance stagger ~0.18–0.26s, first offset 0.10–0.15s. Vary eases.
- **Flagship camera rule (from the airplane):** pan (X) + zoom (Y + scale) move TOGETHER in
  ONE synced ease (`power2.inOut`) so the framed target glides straight to center — never lead
  the pan ahead of the zoom (causes overshoot/swing-back). `transform-origin: 0 0`;
  to frame world point P at scale s, `tx = 540 − s·Px`, `ty = 960 − s·Py`.
- **Motion blur:** Sai's marker carries a directional SVG `feGaussianBlur` (vertical) whose
  stdDeviation is driven up during the fast/overtake phase and back to 0 at the line, plus
  orange speed-trail streaks. A subtle world blur rides the camera move.
- Constant/eased object motion through space; seekable, time-based, finite repeats only;
  no `Math.random()`/`Date.now()`.
- **NO exit animations** (single scene; the Premiere cut ends the card).

## Note on "fewer words"
The 3 bigger competitor markers + Sai's small one tell the story visually — keep text to the
finish banner ("FORTUNE 500"), the "WON" stamp, and minimal labels. On-card text competes with
the burned-in captions ([[feedback_infographics_fewer_words]]).

## Render
- All alpha ProRes 4444. Export to
  `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 8 - Fortune 500 Clients/`.
- Preview each + get Gray's OK BEFORE rendering (locked rule).
