# Client Funnel — Design

Overlay asset for video edits. Five iPhone-style rounded client squares pop up left-to-right across the top, then money funnels down into a single receiving box that grows as money lands. Renders on chroma green for keying in Premiere/AE.

## Style Prompt

Pictogram-style flat white graphics on a flat chroma-green field. iPhone app-icon aspect — rounded-square (squircle-ish) tiles. No rendering, no texture, no gradients. Motion is snappy and comedic — boxes pop in with bounce, dollar signs drop straight down with a tiny squash on landing, the receiver scales up in visible steps as it absorbs.

## Colors

- `#00B140` — chroma green (background, keys cleanly with default Keylight)
- `#FFFFFF` — boxes, text, dollar glyphs
- `#00B140` — label text inside the white squares (cuts back to the chroma color so it reads against white)

## Typography

- `'Montserrat', sans-serif` — labels (matches calendar-month asset)

## Motion

- Client square pop-in: scale 0 → 1 with `back.out(2.0)` over 0.35s, staggered every 0.30s left → right
- Receiver box appears after the last client, scales 0 → 1 with `back.out(1.6)` over 0.4s
- Dollar signs drop from each client downward toward the receiver, ease `power2.in`, ~0.55s travel
- Receiver grows in increments (1.0 → ~1.55) on each money landing, ease `back.out(2.4)`, 0.18s

## What NOT to Do

- No drop shadows, gradients, or 3D effects
- No fade-in/fade-out on the squares — they pop or they don't render
- No background variation — flat `#00B140` only
- No outline-only boxes — solid white fill
