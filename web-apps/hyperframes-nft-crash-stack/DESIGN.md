# NFT Crash Article Stack — DESIGN

## Style Prompt
Cold evidence dump on a chroma-key stage — real news article screenshots thrown one-by-one onto a growing pile at canvas center, each landing at a slightly different jaunty angle like papers slapped on a desk. Strong drop shadows sell the depth. No commentary, no overlays — the headlines speak for themselves. Built for Premiere chromakey.

## Colors
- `#00B140` — chroma green (background, keyed out in post)
- `#FFFFFF` — card body / paper white
- `rgba(0,0,0,0.32)` — primary drop shadow
- `rgba(0,0,0,0.24)` — close drop shadow
- `rgba(255,255,255,0.95)` — 4px white paper border ring

## Typography
- Inherited from article screenshots themselves — no overlay text in this composition.

## Motion
- 6 cards, throw-in cadence `back.out(1.7)`, ~0.55s stagger
- Each landing kicks the pile (prev cards micro-jiggle ±4px / ±0.8°)
- No exit animation — pile holds at end (chromakey-friendly freeze)

## What NOT to Do
- No NFT-specific iconography, JPEGs, or commentary overlays — articles ARE the message
- No green chroma anywhere INSIDE the article images (would key out mid-card)
- No `repeat: -1` ambient motion — chroma stage must be deterministic
- No transition animations between scenes — single-scene composition
- No exit fades — pile must remain on-screen at final frame for Sai to cut to/from
