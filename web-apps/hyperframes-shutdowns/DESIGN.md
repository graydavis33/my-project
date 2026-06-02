# Shutdowns — Visual Identity

## Style Prompt

Modern infographic showing two business models being eliminated. White-outlined pill cards on chroma green for chromakey production. A red rubber stamp slams onto each card in sequence — visualizing what got cut. Calm setup, percussive payoff.

## Colors

- Background (chromakey): `#00B140` chroma green
- Primary line/text: `#FFFFFF` white
- Card translucent fill: `rgba(255,255,255,0.04)`
- Accent (stamp): `#ff3b30` red — keys cleanly against green BG

## Typography

- Display: Montserrat 800 — uppercase card labels
- Stamp: Montserrat 900 italic — uppercase, tight tracking

## Motion

- Card entrances: `back.out(1.6)` from x-offset
- Stamp impact: scale 3→1 with `back.out(2.6)` over 0.25s
- Card shake on impact: ±5px x, ±1.5° rotation, 0.06s yoyo ×4
- Hold ~3s after second stamp before final fade

## What NOT to Do

- No green elements inside the asset (key bleed)
- No exit animations between scene beats — single continuous scene
- No emoji or stock illustration
- Stamp must stay opaque red, not gradient (banding on chromakey)
