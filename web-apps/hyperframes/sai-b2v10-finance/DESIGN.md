# Sai Batch 2 Vid 10 — Rebuilding Company Finances — Step Cards

Source: **C2583** ("Redoing finance", Vid 10). 5-step framework (whiteboard:
1 Stress · 2 Ideal · 3 Fundamentals · 4 Rebuild · 5 Hire a CPA).
Same locked Sai HyperFrames brand style as Vid 7 (`sai-b2v7-nfts/`) and Vid 4.

## Format
- 1080×1920 vertical, 24fps
- **Transparent background** (orange-glass has glow + soft drop shadow → render
  ProRes 4444 alpha `.mov` per the locked rule; no chroma-key).
- Standalone composition per step folder, one preview port each.

## The cards
One centered **orange-glass card** per step:
- white circle **number badge** (1–5)
- small tracked **STEP N** kicker label
- big white **hero word** (the whiteboard term: STRESS / IDEAL / FUNDAMENTALS /
  REBUILD / HIRE A CPA)

## Colors (locked)
- Trendify orange `#F28129` — glass card body (gradient `#FFA858 → #F28129 → #D66416`)
- White `#FFFFFF` — text, badge fill, 2px card border
- Orange-glass recipe: radial top highlight + linear orange gradient, `2px solid #fff`
  border, inset highlights + `0 0 24px rgba(242,129,41,0.55)` glow +
  `0 8px 22px rgba(0,0,0,0.30)` drop shadow.

## Typography
- **Montserrat** — Black (900) hero word + badge, ExtraBold (800) kicker, UPPERCASE
- Hero word 64–120px (size per word so it fits the card), kicker ~34px, badge ~58px

## Motion
- Card pops in (`back.out(1.5)` + scale), badge `back.out(1.8)`, kicker + word stagger up
- Single-scene card → **NO exit animation** (the Premiere cut ends it)
- Time-based / seekable, finite repeats only

## What NOT to do
- No emojis, no green elements, no `<br>` mid-line, no system fonts, no exit anim
- No `Math.random()` / `Date.now()`
