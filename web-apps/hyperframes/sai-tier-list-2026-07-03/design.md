# Sai Tier List — Design Spec

Overlay graphic for the Sai "business advice tier list" short. Composites over Sai's
talking-head A-roll (1080x1920). Reference: Hormozi business-book tier list (classic
TierMaker grid, colored tier labels, dark rows, item pops in large then flies to its slot).

## Placement

- Tier board sits ABOVE Sai's head — top of frame, roughly y 70–555. Sai's head top ≈ y 590.
- Burned-in captions live mid-frame (~y 1140) — nothing sustained there except the brief
  item intro pop (matches the reference, which overlaps the subject).

## Colors

- Background: chroma green `#00FF00` (keyed in Premiere)
- Tier label colors (classic TierMaker, per the reference):
  S `#FF7F7E` · A `#FFBF7F` · B `#FFDF80` · C `#FEFF7F` · D `#BEFF7E` · F `#7EFF80`
  ⚠ D and F are green-family — if the chroma key grabs them in Premiere, shift them via
  Studio variables (they're exposed).
- Row background: `#191918` (solid dark, like the reference)
- Item cards: `#26262B` dark card, white drawn SVG icons (NO emojis — locked Sai rule)
- Text: white `#FFFFFF`, tier letters dark `#191918` on their color chip

## Typography

- Montserrat SemiBold (600) for item titles, Bold (700) for tier letters
- Title drop shadow: `0 2px 8px rgba(0,0,0,0.4)`

## Output

- 1080x1920, 60fps, chroma-green MP4 (hard-edged shapes → green is correct, no alpha needed)
- data-duration 68s = full length of the raw draft (67.4s) so the board persists as one
  exported layer Gray drops over the whole video
- Delivery: `/Volumes/Footage/Sai/06_ASSETS/Visual Effects/<batch folder TBD>/Sai-VFX-Tier-List-Board.mp4`

## The 9 items (from the raw transcript, timed to Sai's audio)

| # | Item | Tier | intro (s) | fly (s) |
|---|------|------|-----------|---------|
| 1 | Extend your time horizon | S | 0.10 | 1.12 |
| 2 | Obsess over customers | S | 3.25 | 4.56 |
| 3 | Raising money | C | 10.25 | 10.90 |
| 4 | Systems first | A | 17.45 | 18.26 |
| 5 | Learn how to sell | D | 22.70 | 23.46 |
| 6 | Micromanagement | F | 34.80 | 35.22 |
| 7 | Culture is king | S | 40.25 | 41.08 |
| 8 | Personal brand | B | 48.30 | 48.92 |
| 9 | AI tools | B | 55.60 | 56.24 |

Raw video: `/Volumes/Footage/Sai/03_DELIVERED/drafts/transcribe and add effects.mp4`
Reference: `/Volumes/Footage/Sai/Screen Recording 2026-07-03 at 17.58.02.mov` (Hormozi IG post)

## Animation per item

1. Board is on screen from t≈0 (staggered row slide-in, once).
2. At intro time: item card pops in LARGE (back.out) low-left of frame + title text
   slides in beside it.
3. At fly time (the moment Sai says the tier): title fades, card shrinks + flies into
   the next open slot in its tier row (power2.inOut), lands with a scale settle,
   row label pulses + row background flashes.

`itemsToShow` variable gates how many items run (default 1 while Gray reviews effect #1;
set to 9 for the full pass).
