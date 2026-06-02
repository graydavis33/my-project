# Design — Social Counters

## Style Prompt
Three platform-branded counter graphics for use as overlay assets in Premiere. Each composition shows the platform logo (accurate brand mark), a count-up number animation, and a small label. Transparent background so the assets composite cleanly over any footage. Modern, restrained, motion-driven — the brand colors do the heavy lifting; everything else stays clean.

## Compositions
| Composition | Dimensions | Duration | Purpose |
|---|---|---|---|
| `tiktok-counter` | 1080×1080 | 4s | TikTok logo + animated count |
| `instagram-counter` | 1080×1080 | 4s | Instagram logo + animated count |
| `youtube-counter` | 1080×1080 | 4s | YouTube logo + animated count |
| `index.html` (preview) | 3240×1080 | 4s | Side-by-side preview of all three |

Each sub-composition is standalone and can be rendered solo for use as an individual overlay asset.

## Colors

### TikTok
- Canvas: transparent
- Primary text/logo body: `#FFFFFF` white (used on transparent — appears as the logo glyph color)
- Magenta accent: `#FE2C55` (offset glyph layer)
- Cyan accent: `#25F4EE` (offset glyph layer)
- Counter text: `#FFFFFF`

### Instagram
- Canvas: transparent
- Gradient stops (matches official Instagram brand gradient):
  - `#F58529` — orange
  - `#FEDA77` — yellow
  - `#DD2A7B` — pink/magenta
  - `#8134AF` — purple
  - `#515BD4` — blue/indigo
- Logo stroke: gradient
- Counter text: `#FFFFFF`

### YouTube
- Canvas: transparent
- Primary: `#FF0000` (YouTube red)
- Logo body: `#FF0000`, play triangle: `#FFFFFF`
- Counter text: `#FFFFFF`

## Typography
- Counter numbers: `Inter`, weight 800, `font-variant-numeric: tabular-nums` (no jitter on tick), 180px
- Labels: `Inter`, weight 600, 36px, `letter-spacing: 0.12em`, `text-transform: uppercase`

## Motion
- **Logo entrance** (0.0s → 0.5s): scale from 0.8 + fade in, `back.out(1.4)` ease
- **Counter entrance** (0.4s → 0.6s): fade in + slide up 30px, `power3.out`
- **Number tween** (0.6s → 3.0s): count from 0 → target value, `power2.out` ease, snapped to whole integers
- **Hold** (3.0s → 4.0s): all elements fully visible (per house style — no exits in middle scenes; the final hold IS the exit context for the asset)

## What NOT to Do
- No drop shadows on the YouTube red play button — it's already saturated; shadow muddies it
- No re-coloring the Instagram gradient — use the official 5-stop palette in the documented order
- No animated rotation on logos — they're brand marks, not playful elements
- No gradients across the entire 1080×1080 canvas (H.264 banding on transparent renders)
- No `repeat: -1` on the count tween — it's a single 0-to-target sweep
