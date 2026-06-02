# Sai Shorts — Brand Design System

Brand kit for Sai talking-head shorts motion graphics. Video: "Two things have to be true before you scale."

## Palette
- **White** — `#FFFFFF` — primary text, strokes, base
- **Orange** — `#F28129` — accent, highlights, brand color
- Background is **chroma green** `#00FF00` — Gray keys it out in his NLE.
- **Chroma color rule:** if ANY element in a comp is green at any point, switch the background to chroma BLUE `#0047BB` instead, so the keyer doesn't erase the asset. (None of these comps should need green — keep to white + orange.)

## Typography
- **Family:** Montserrat (built into HyperFrames — no font files needed)
- **Weight:** Semibold 600 for body, ExtraBold 800 / Black 900 for display
- **Color:** White `#FFFFFF`
- **Effect:** subtle drop shadow on white text: `text-shadow: 0 2px 8px rgba(0,0,0,0.4);`

## Shape Style
- **Strokes:** thin white (2–3px) on graphical containers
- **Corners:** `border-radius: 24–36px` cards, `border-radius: 999px` pills
- **Fill:** transparent or solid/orange-glass
- **Orange-glass card** (for emphasis cards/pills):
  background: radial specular at top + linear orange body gradient (light→mid→dark),
  border: 3px white, box-shadow: inner top highlight + inner bottom shadow + outer orange bloom + base drop shadow.
- **Drop shadow (containers):** `box-shadow: 0 8px 24px rgba(0,0,0,0.28);`

## Output Defaults
- **Dimensions:** 1080 × 1920 (vertical 9:16)
- **Background:** `#00FF00` chroma green
- **FPS:** render at 60
- **Render duration** comes from `data-duration` on root.

## A-Roll Constraint
All graphics composite OVER Sai's centered talking-head A-roll. Use top third or lower third for sustained text; full-screen "punch" overlays OK for brief 0.5–1s number/word hits. Keep the vertical-center face zone (roughly Y 700–1300) relatively clear for sustained elements when possible.

## What NOT to Do
- No drop shadows so heavy they read as bevels
- No gradient *backgrounds* (H.264 banding) — radial/solid + localized glow only
- No colors outside white + orange + chroma-green
- No neon glow that bleeds into chroma-key edges
- No serif or script fonts
