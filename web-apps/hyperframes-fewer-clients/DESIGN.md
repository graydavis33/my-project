# Design — Sai HyperFrames Asset House Style

## Style Prompt
Clean white-only infographic on a flat chroma green background, designed to be keyed out in post-production. Bold sans-serif typography with wide letter-spacing for emphasis labels. Crisp geometric shapes (stick figures, rings, arrows) with no textures, no gradients, no shadows. Motion is snappy with `back.out` pop-ins, deliberate `power2.out` draws on outline strokes, and rhythmic pulse rings.

## Colors
- `#00B140` — chroma green canvas (keying color, never appears as a graphic element)
- `#FFFFFF` — single ink color for ALL graphics, text, and strokes

## Typography
- `Inter` — primary sans, 800 (ExtraBold) for headlines and number labels, 700 (Bold) for caption labels
- Letter-spacing `0.18em` on uppercase labels for poster-feel weight

## Motion
- Pop-ins: `back.out(2.0)` 0.55s, scale 0→1 + opacity 0→1
- Path draws: `power2.out` 0.50s, `stroke-dashoffset` from length→0
- Pulse rings: scale 1→1.4 + opacity 0.8→0, `power2.out` 1.4s, 3 staggered rings
- Stagger entrances: 100-200ms between siblings
- 60fps render for smooth scale + path-draw motion

## What NOT to Do
- No green graphic elements (would key out alongside the BG)
- No gradients, drop-shadows, or blur effects
- No second color outside white
- No `repeat: -1` infinite loops — always finite repeat counts
- No `stroke-linecap: round` on a hidden-via-dashoffset path without snapping opacity to 1 at draw start (renders a phantom dot at path origin)
- No `gsap.fromTo` at non-zero start time without `immediateRender: false` (else "from" state applies at script load)
