# Sai Batch 2 Vid 4 — Fire Sirens / Acceptance — Title-Hook Graphics

Brand spec for the on-screen TITLE-HOOK cards for Vid 4 (C2573, "acceptance" /
8th Ave sirens). Three trial-reel title cards, one per hook. Matches the locked Sai
title-card style (`sai-c2496-three-buckets/g1-only-3-title`).

## Format
- 1080×1920 vertical, 24fps
- **Chroma green `#00FF00` background** — keyed out in Premiere (Ultra Key); the
  white/orange title text floats over Sai's A-roll. No green on any visible element.
- ~3.5s each, single scene, standalone composition (no `<template>`).

## Colors
- **Trendify orange** `#F28129` — the emphasis word/line in each title (the SEO hook)
- **White** `#FFFFFF` — the rest of the headline
- **Chroma green** `#00FF00` — background only

## Typography
- **Montserrat ExtraBold/Black (800–900)**, UPPERCASE, letter-spacing −0.01em
- Headline lines 72–96px; orange hero word up to ~150px
- Drop shadow `0 6px 18px rgba(0,0,0,0.45)` (white), `0 10px 32px rgba(0,0,0,0.5)` (orange)
- One line per `<div>` (deliberate breaks — never `<br>`)

## Motion
- Line-by-line entrance, stagger ~0.18–0.26s, first offset 0.15s
- Vary eases: `power3.out`, `back.out(1.6)`, `power2.out`, `expo.out`
- Orange hero word pops via `back.out(1.8)` + slight scale
- Single scene → NO exit animations (the cut in Premiere ends it)

## The 3 cards
1. **title-1-annoying-sound** — "The most annoying sound in NYC taught me my biggest life lesson" (hero: LIFE LESSON)
2. **title-2-cant-control** — "Stop letting things you can't control steal your peace" (hero: YOU CAN'T CONTROL)
3. **title-3-acceptance** — "Why acceptance is the skill that changed everything" (hero: ACCEPTANCE)

## What NOT to do
- No `#333`/`#3b82f6`/Roboto/system fonts — Montserrat only
- No green on visible elements
- No exit animations (single scene)
- No `<br>` mid-line — one div per line
- No infinite repeats
