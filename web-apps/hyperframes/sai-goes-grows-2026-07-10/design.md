# Sai — Goes vs Grows T-Chart

Overlay graphic for Sai's short "what I thought would grow my business vs. what actually did."
Clean white T-chart, **GOES** (left = the myths he ditched) / **GROWS** (right = what actually worked).
Each phrase pops in a colorful rounded-square logo tile on its side, cumulatively (chart fills up).

- **Source audio:** `/Volumes/Footage/Sai/03_DELIVERED/drafts/5 growth tactics.aac` (32.8s)
- **Transcript:** `transcript.json` (whisper large-v3, word-level)
- **Format:** 1080×1920, 60fps, 33s. GOES tiles = warm (red/orange). GROWS tiles = green/teal/blue.
- **Icons:** drawn white line SVGs (no emojis — brand rule).

## The 5 pairs (times = tile pop, seconds)

| Slot | GOES (left) | pop | GROWS (right) | pop |
|---|---|---|---|---|
| 0 | Running Ads | 2.5 | Great Product | 4.6 |
| 1 | AI Agents | 6.6 | Great People | 9.2 |
| 2 | Hire a CPA | 10.9 | Master the Numbers | 15.6 |
| 3 | New Clients | 20.0 | Upsell Clients | 23.0 |
| 4 | DIY Onboarding | 25.2 | Systems & Checklists | 28.7 |

Timings live in the `ITEMS` array in `index.html`. Item 1 (Running Ads) pop time is also a
Studio variable (`item1Time`) for a quick live nudge. `itemsToShow` = 1 for review, 10 for full.

## Deliverables
Rendered 60fps → `/Volumes/Footage/Sai/06_ASSETS/Visual Effects/Batch 4/`
- `Sai-VFX-GoesVsGrows-GREEN.mp4` — chroma green, key it in Premiere
- `Sai-VFX-GoesVsGrows-ALPHA.mov` — ProRes 4444 transparent, drop straight over Sai

## Re-render
- Green: `npm run render` (bg is `#00FF00`)
- Alpha: swap body `background` to `transparent`, then `npx hyperframes render --fps 60 --format mov`, then restore green.
