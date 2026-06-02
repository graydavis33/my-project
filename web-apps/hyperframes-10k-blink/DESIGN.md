# $10,000 Blink Green — Visual Identity

## Style Prompt

Sai brand asset. Bold dollar-amount type that pops in white, flashes green twice, then locks solid green for the remainder of the clip. Chroma BLUE background (not green) since the asset itself turns green — green key would erase the lock-in moment.

## Colors

- `#0047BB` — chroma blue canvas (background, keys out cleanly with Ultra Key)
- `#FFFFFF` — white (initial state of "$10,000")
- `#00B140` — brand green (final/locked state, also flash color)

## Typography

- **Montserrat 600 (SemiBold)** — "$10,000", tabular numerals

## Motion

- Pop-in: scale + opacity from 0, `back.out(1.6)` overshoot
- Hold white briefly
- Two sharp blinks (instant `tl.set` color flips, no easing — looks like a sign turning on)
- Lock to green permanently with a small scale punch on the lock moment
- Hold green to end of clip

## What NOT to Do

- No gradient/fade between white and green — sharp instant flips
- No green-tint flash that lingers — each flash is one frame
- No exit animation — once green, stays green
- No drop shadows or glow on the type
