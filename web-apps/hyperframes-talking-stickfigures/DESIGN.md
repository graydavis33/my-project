# Talking Stick Figures — Design

Overlay asset for video edits. Two half-body white stick figures appear to talk back and forth with gibberish speech bubbles. Renders on chroma green for keying in Premiere/AE.

## Style Prompt

Pictogram-style flat silhouettes against a flat chroma-green field. White figures, no rendering or texture. Speech bubbles are flat white with a rounded body and a small triangular tail pointing down to the speaker. Gibberish text uses high-contrast black symbols inside the bubble. Motion is comedic and snappy — small wiggles, quick pops, no easing into stillness.

## Colors

- `#00B140` — chroma green (background, keys cleanly with default Keylight)
- `#FFFFFF` — figure silhouette + speech bubble fill
- `#000000` — gibberish text

## Typography

- `'JetBrains Mono', 'Courier New', monospace` — gibberish symbols (mono keeps random symbols evenly spaced and clearly non-linguistic)

## Motion

- Figure wiggle while speaking: ±3° rotation, ±4px Y bounce, ~0.15s per cycle, ~4 cycles per turn
- Bubble pop-in: scale 0 → 1 with `back.out(2.0)` over 0.18s
- Bubble pop-out: scale 1 → 0 with `back.in(1.6)` over 0.14s
- Idle figure: completely still while the other speaks

## What NOT to Do

- No drop shadows, gradients, or 3D effects on figures or bubbles
- No fade-in/fade-out on the figures themselves — they should be present and crisp the whole clip so the asset can be cut anywhere on the editor's timeline
- No real words or recognizable letters in the bubbles — only symbols
- No background variation or texture — flat `#00B140` only, otherwise keying breaks
