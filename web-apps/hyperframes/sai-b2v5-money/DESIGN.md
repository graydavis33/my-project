# Sai Batch 2 Vid 5 — How I Manage My Money — Graphics Package

> ⭐ **FLAGSHIP REFERENCE: `ig-3-emergency-fund/` (the airplane runway).** Gray starred this
> as one of our most important + advanced animations — the benchmark for the cinematic,
> engaging "AE-3D" motion-graphics style we want to keep making (camera pan+zoom synced with
> no overshoot, object moving through space). Use it as the bar for future infographics.
> See memory `feedback_prefers_3d_motion_graphics.md`.

Source: **C2574** ("How I manage my money", Vid 5). Same locked Sai HyperFrames brand
style as Vid 9 (`sai-b2v9-mentors/`), Vid 7, Vid 4.

## Final spoken content (from transcript)
- Hook: blew **90%** of his money at **18** → here's the system now
- Allocation: **30% cash** (a vault "Emergency Fund" w/ **6 months** runway) ·
  **40% basic indexes + treasuries** · **30% long-term + riskier stocks**
- Habit: budget monthly + follow it; review spending **weekly**; deep-dive total assets
  **monthly**; *"you can only change something if you track it"*
- (The "10% physical assets" line from the draft was CUT in the final — not included.)

## Script beats → infographics
- "blew 90% of my money at 18" → **ig-1-blew-90**
- the 30/40/30 allocation → **ig-2-allocation** (hero — donut chart)
- emergency fund, 6-month runway → **ig-3-emergency-fund**
- "you can only change what you track" → **ig-4-track-it**

## Format
- 1080×1920 vertical, 24fps
- **Transparent background** (orange-glass glow + soft drop shadows → render ProRes 4444
  alpha `.mov`; no chroma-key).
- Standalone composition per folder (no `<template>`), one preview port each.

## Colors (locked)
- **Trendify orange** `#F28129` — primary emphasis, mid chart tone
- Light orange `#F2B66A` / deep orange `#C8631A` / deepest `#B2540F` — chart shade ramp
- **White** `#FFFFFF` — text, figures, badges
- **Crash red** `#E63946` — the "lost/blown" money (ig-1)
- Orange-glass recipe: radial top highlight + linear orange gradient
  (`#FFA858 → #F28129 → #D66416`), `2px solid #fff` border, inset highlights +
  `0 0 24px rgba(242,129,41,0.55)` glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow.

## Typography
- **Montserrat** — Black (900) hero numbers/%, ExtraBold (800) labels, UPPERCASE,
  letter-spacing −0.01 to −0.02em
- Hero number/% 90–150px, labels 34–52px; `tabular-nums` on number columns
- Drop shadows `0 4px 14px rgba(0,0,0,0.45)`; one line per `<div>` (no `<br>` mid-line)

## Motion (single-scene cards)
- Entrance only, stagger ~0.18–0.26s, first offset 0.10–0.15s
- Vary eases: `back.out(1.5–1.8)`, `power3.out`, `power2.out`, `expo.out`
- Donut arcs draw in sequence (stroke-dashoffset); numbers pop with `back.out`
- **NO exit animations** (single scene; the Premiere cut ends the card)
- Time-based / seekable, finite repeats only; no `Math.random()`/`Date.now()` (seed if needed)

## Note on "fewer words"
Money beats are data — short labels + the numbers ARE the content (per
[[feedback_infographics_fewer_words]] this is allowed: minimal text, the visual/number carries it).
Keep legends to 1–3 words + the figure.

## Render
- All alpha ProRes 4444. Export to `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 5 - How I Manage My Money/`.
- Preview each + get Gray's OK BEFORE rendering (locked rule).
