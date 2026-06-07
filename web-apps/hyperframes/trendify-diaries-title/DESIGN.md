# Trendify Diaries — Title Sequence · Design

Title card for the Sai BTS documentary (Ep 1). Drops over the cold-open footage as an alpha overlay.

## Style Prompt
Clean, cinematic docuseries title card. White type on transparent, a soft center scrim so it reads over any footage. Restrained, premium motion — a mask wipe-up on the wordmark, a hairline rule drawing out, an elegant letter-by-letter reveal on the episode label. No color, no clutter. The motion is the "cool," not decoration.

## Colors
- `#FFFFFF` — all type (white), per Gray's direction
- `rgba(0,0,0,0.55)` — center scrim (alpha; darkens footage behind the title only)
- (optional brand nod, not used by default) `#F28129` — Trendify orange, available for the divider if wanted

## Typography
- **Montserrat SemiBold (600)** — the only typeface. Wordmark wide-tracked; episode label very wide-tracked, uppercase.

## Motion
- Wordmark: mask reveal (slides up from behind an overflow mask), `power4.out`
- Divider: scaleX draw from center, `power3.inOut`
- Episode label: per-letter staggered rise + fade, `power3.out`
- Single scene → only the final fade-out is an exit

## What NOT to Do
- No second font, no bold/black weight mixing — SemiBold throughout
- No solid background baked in — must stay alpha for compositing
- No bouncy/elastic eases — this is restrained and cinematic
- No drop shadows keyed on green (render alpha ProRes 4444, not chroma)
