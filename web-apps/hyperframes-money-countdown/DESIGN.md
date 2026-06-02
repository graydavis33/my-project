# Design — Sai HyperFrames Asset House Style

## Style Prompt
Clean white-only infographic on a flat chroma green background. Single icon paired with a large dollar amount that whips down slot-machine style and lands on a meaningful figure. Bold sans-serif typography with tabular figures so the digits stay aligned during the countdown. No textures, gradients, or shadows.

## Colors
- `#00B140` — chroma green canvas (keying color)
- `#FFFFFF` — single ink color for graphic + text

## Typography
- `Inter` ExtraBold (800) for the dollar amount — `font-variant-numeric: tabular-nums` to keep digits stable
- `Inter` ExtraBold (800) for the `$` glyph inside the money-sign circle

## Motion
- Synchronized fade entrance (no sequencing) — graphic + number appear together, graphic also rises from below
- Slot-machine count via GSAP onUpdate, formatted with commas on every frame
- `power3.out` ease decelerates the count into the final landing number
- 60fps render

## What NOT to Do
- No green graphic elements
- No bouncing, scaling pulses, or yoyo emphasis on the final number
- No `repeat: -1` infinite loops
- No gradients, drop-shadows, or texture
