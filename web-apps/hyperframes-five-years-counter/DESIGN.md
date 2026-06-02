# Five-Years Counter — Visual Identity

## Style Prompt

Graydient Media brand asset. Bold, confident typographic counter on chroma green for keying in Premiere. Single hero element on canvas — slot-machine number rolls 1→5, then "years" lands beside the 5. Pure type, no decoration. Reads instantly even at thumbnail scale.

## Colors

- `#00B140` — chroma green canvas (background, keys out)
- `#FFFFFF` — white (numbers + "years" type)

## Typography

- **Montserrat 600 (SemiBold)** — all text, white, tabular numbers for the counter

## Motion

- Slot-machine ticks: each digit drops in from above with `back.out(2.2)` overshoot, prior digit drops out below
- Tick cadence: ~0.25s per number (1→2→3→4→5)
- "years" entrance: slides in from offscreen left to position right of the 5, `power3.out` (smooth deceleration)
- Hold the final "5 years" frame ~1.2s before end

## What NOT to Do

- No background gradients, glows, or decorative elements (chroma green must stay solid for keying)
- No color other than white on the type (single-color key-friendly asset)
- No fade-in on the digit ticks — they DROP, they don't fade
- No exit animation on "years" — it lands and stays through end of clip
- No serif or alternate fonts — Montserrat SemiBold only
