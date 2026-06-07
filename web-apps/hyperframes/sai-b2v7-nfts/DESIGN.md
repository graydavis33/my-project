# Sai Batch 2 Vid 7 — Identity Equals NFTs — Graphics Package

Source: **C2578** ("Identity equals NFTs", Vid 7). Same locked Sai HyperFrames brand
style as Vid 4 fire-sirens (`sai-b2v4-firesirens/`). Lean package (Gray's call):
3 hook title cards + 3 beat infographics.

## Format
- 1080×1920 vertical, 24fps
- **Chroma green `#00FF00` background** — keyed out in Premiere (Ultra Key). No green
  on any visible element.
- Standalone compositions (no `<template>`), one per folder, each on its own preview port.

## Colors
- **Trendify orange** `#F28129` — emphasis word / orange-glass cards (the SEO/payoff hook)
- **White** `#FFFFFF` — primary headline text, card text, drawn figures
- **Crash red** `#E63946` — loss / "nothing" / market collapse
- **Chroma green** `#00FF00` — background only
- Orange-glass recipe (cards/pills): radial top highlight + linear orange gradient,
  `2px solid #fff` border, inset highlights + `0 0 24px rgba(242,129,41,0.55)` glow +
  `0 6px 18px rgba(0,0,0,0.28)` drop shadow.

## Typography
- **Montserrat** — ExtraBold/Black (800–900), UPPERCASE, letter-spacing −0.01 to −0.02em
- Title headline lines 50–72px; orange hero word 108–150px
- Drop shadows `0 6px 18px rgba(0,0,0,0.45)` (white), `0 12px 36px rgba(0,0,0,0.5)` (orange)
- One line per `<div>` (deliberate breaks — never `<br>`)

## Motion
- Line/element entrance, stagger ~0.18–0.26s, first offset 0.10–0.15s
- Vary eases: `power3.out`, `back.out(1.6–1.8)`, `power2.out`, `expo.out`
- Orange hero word pops via `back.out(1.7)` + scale
- Single-scene cards → NO exit animations (the Premiere cut ends them)
- All motion time-based / seekable, finite repeats (no `repeat:-1`)

## The 6 cards
1. **title-1-million** — Hook A. "$1,000,000 liquid at 17 — and I'm glad I didn't" (hero: $1,000,000)
2. **title-2-nft-project** — Hook B. "An NFT project for millions at 17 — glad it didn't work out" (hero: AN NFT PROJECT)
3. **title-3-divine** — Hook C. "A divine intervention by the gods of business" (hero: DIVINE INTERVENTION)
4. **ig-1-school-stages** — drawn 3-step ascending staircase: ELEMENTARY (fit in) →
   MIDDLE (be smarter) → HIGH SCHOOL (the future); throughline = always proving myself.
5. **ig-2-market-collapse** — animated line graph: exponential climb (orange) → brutal
   crash (red) right before launch, red X stamp + "COLLAPSED". Adapted from
   `sai-shorts-2026-05-27/batch1-vid7/02-business-crash-graph`.
6. **ig-3-lesson** — drawn split-contrast infographic (NO equation text): two
   orange-glass panels, "FOR THEM" vs "FOR YOU", using the locked head+shoulders
   avatar (upper body, round head — from `sai-b2v4-firesirens/ig-7`). LEFT = a
   speaker talking (animated mouth + speech bubble) to 3 listener avatars; a red
   ✗ pops in (fixed position) and the whole card does one natural red blink. RIGHT
   = one avatar with static shine lines from the head; a green ✓ pops in ~1.6s
   later and the whole card does one smooth ~1s green blink. Only continuous
   motion = the speaker's mouth. Green ✓/blink ⇒ this card is ALPHA-only (a green
   element can't be chroma-keyed). 5.0s. Exported:
   `6 - The Lesson (For Them vs For You) (alpha).mov`.

## Render modes (per locked rule: alpha when soft drop shadows present)
- **Titles (1–3):** green-screen MP4 — keyed in Premiere (text shadows key clean enough).
- **ig-1, ig-3 (orange-glass + box-shadow glow):** ProRes 4444 alpha `.mov`.
- **ig-2 (white card + drop shadow):** ProRes 4444 alpha `.mov`.
- Exports land in `D:/Sai/06_ASSETS/Visual Effects/Batch 2 Vid 7 - Identity NFTs/`.

## What NOT to do
- No emojis — drawn SVG infographics only (locked rule)
- No `#333`/`#3b82f6`/Roboto/system fonts — Montserrat only
- No green on visible elements
- No exit animations (single scene)
- No `<br>` mid-line — one div per line
- No infinite repeats; no `Math.random()`/`Date.now()`

## Workflow
Preview each in the studio and get Gray's OK BEFORE rendering (locked rule). Then render
+ export to the Sai assets bucket above.
