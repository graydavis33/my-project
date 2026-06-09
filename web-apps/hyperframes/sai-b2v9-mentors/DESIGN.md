# Sai Batch 2 Vid 9 — The Story of Neil and Mike (Why Mentors Matter) — Graphics Package

Source: **Vid 9** ("Neil and Mike / why mentors matter"). Same locked Sai HyperFrames
brand style as Vid 7 (`sai-b2v7-nfts/`), Vid 10 (`sai-b2v10-finance/`), and Vid 4.
Lean package: **3 beat infographics** (drawn, no title cards unless Gray asks).

## Script beats → infographics
- *"two mentors who run an agency that employs over 800 people"* → **ig-1-eight-hundred**
- *"lunch with two mentors… genuinely curious about me"* → **ig-2-money-vs-people**
  (folder name is legacy; content is now: two mentor figures TALKING to one figure (you) —
  animated mouths, head bobs, alternating speech bubbles; you listen w/ a nod + small smile)
- *"it has nothing to do with the material… it makes you want to be a better person"*
  → **ig-3-north-star**
- building wealth into an empire (extra graphic Gray requested) → **ig-4-skyscraper**
  (3 BIG $ signs ease/fade/pop in + hold → realistic setback tower rises out of the money
  as the $ fade → holds "obviously built" → collapses straight down (no shake, no fade): the
  tower buckles/sinks while a solid jagged rubble mound rises to swallow it + dense seeded crumb
  texture on top (thick pile, no gaps) + dust. No camera move. HTML facade sections.
  **Rendered at 60fps** per Gray, transparent ProRes 4444.)

## Format
- 1080×1920 vertical, 24fps
- **Transparent background** (orange-glass glow + soft drop shadows → render ProRes 4444
  alpha `.mov` per the locked rule; no chroma-key).
- Standalone composition per folder (no `<template>`), one preview port each.

## Colors (locked)
- **Trendify orange** `#F28129` — emphasis, orange-glass cards/pills, the "good" path
- **White** `#FFFFFF` — primary text, drawn figures, badges
- **Crash red** `#E63946` — the "money-only / bored" trap path, the decline line
- Orange-glass recipe: radial top highlight + linear orange gradient
  (`#FFA858 → #F28129 → #D66416`), `2px solid #fff` border, inset highlights +
  `0 0 24px rgba(242,129,41,0.55)` glow + `0 8px 22px rgba(0,0,0,0.30)` drop shadow.

## The locked avatar (reused from `sai-b2v4-firesirens/ig-7`)
Head + shoulders bust, solid silhouette, round head, no legs:
- head `circle cx=540 cy=752 r=146`
- bust `path d="M 352 1300 Q 352 1000 448 938 Q 494 910 540 908 Q 586 910 632 938 Q 728 1000 728 1300 Z"`
Defined as `#avatarShape` in `<defs>`, drawn via `<svg viewBox="345 598 390 712"><use href="#avatarShape"/></svg>`, colored by CSS `fill`.

## Typography
- **Montserrat** — Black (900) hero numbers/words, ExtraBold (800) labels/kickers, UPPERCASE,
  letter-spacing −0.01 to −0.02em
- Hero number/word 90–150px, labels 36–58px, kickers ~38px
- Drop shadows `0 4px 14px rgba(0,0,0,0.45)`; one line per `<div>` (no `<br>` mid-line)

## Motion (single-scene cards)
- Entrance only, stagger ~0.18–0.26s, first offset 0.10–0.15s
- Vary eases: `back.out(1.5–1.8)` (cards/badges), `power3.out`, `power2.out`, `expo.out`
- Hero number/badge pops via `back.out` + scale; crowd/graph fills via small stagger
- **NO exit animations** (the Premiere cut ends the card)
- All motion time-based / seekable, finite repeats only

## Render modes
- All three have orange-glass glow / soft drop shadows → **ProRes 4444 alpha `.mov`**.
- Exports land in `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 9 - Neil and Mike/`.

## What NOT to do
- No emojis — drawn SVG / Montserrat glyphs only
- No green elements (alpha render, not chroma)
- No `#333`/`#3b82f6`/Roboto/system fonts — Montserrat only
- No exit animations, no `<br>` mid-line
- No `Math.random()` / `Date.now()` — seed any pseudo-random (none needed here)

## Workflow
Preview each in the studio and get Gray's OK BEFORE rendering (locked rule). Then render
+ export to the Sai assets bucket above.
