# NBA + CEO + Celebrity → NFT Project — Visual Identity

## Style Prompt

Sai brand asset. Equation-style infographic: three white outlined icons separated by white plus signs, all popping in left-to-right with a satisfying overshoot. After a hold, the row converges inward and an NFT Project icon bursts out at center. Pure white-on-chroma, keys cleanly.

## Colors

- `#00B140` — chroma green canvas (background, keys out)
- `#FFFFFF` — white (all icons, labels, plus signs)

## Typography

- **Montserrat 600 (SemiBold)** — labels and "NFT PROJECT" headline, white, all caps

## Motion

- Icon pop-in: scale 0 → 1 + opacity 0 → 1, `back.out(2.0)`, ~0.4s each
- Plus pop-in: same easing, ~0.3s
- Sequenced left-to-right with ~0.30s spacing
- Hold the full equation visible ~1.6s
- Merge: each element converges toward canvas center (x-delta + scale 0.2 + opacity 0), `power3.in`, 0.35s — feels like collision/fusion
- NFT entrance: scale 0 → 1 + opacity 0 → 1, `back.out(2.0)`, 0.55s
- NFT label slides up + fades after hexagon settles

## What NOT to Do

- No fill on icons that should read as outlines (basketball, $-circle, hexagon)
- No drop shadows or glows (chroma green must stay solid)
- No color other than white
- No exit animation on NFT — once out, stays through end of clip
