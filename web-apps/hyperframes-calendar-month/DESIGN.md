# One-Month Calendar — Visual Identity

## Style Prompt

Sai brand infographic. White rounded-square calendar grid (6×5 = 30 days) on chroma green for keying. Day cells pop in one at a time with a satisfying overshoot, then "ONE MONTH" headline reveals above the grid. Pure typographic + geometric — no decoration, no shadows, keys cleanly.

## Colors

- `#00B140` — chroma green canvas (background, keys out)
- `#FFFFFF` — white (day cells + headline)

## Typography

- **Montserrat 600 (SemiBold)** — headline, white, all caps

## Motion

- Day cells: `back.out(2.0)` overshoot pop, scale + opacity from 0, 0.04s stagger across 30 cells
- Headline: `power3.out` slide-up + fade after grid completes
- Hold final composition ~1s

## What NOT to Do

- No background gradients or glows (chroma green must stay solid)
- No drop shadows on cells (won't key cleanly)
- No color accents — pure white-on-green
- No gradient fades on the headline — slide + opacity only
