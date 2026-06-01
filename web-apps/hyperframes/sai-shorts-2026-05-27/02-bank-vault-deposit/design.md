# Sai Shorts — Brand Design System

Brand kit for the Sai talking-head shorts motion graphics batch (2026-05-27 onward).

## Palette

- **White** — `#FFFFFF` — primary text, strokes, base
- **Orange** — `#F28129` — accent, highlights, brand color

Background for these compositions is **chroma green** `#00FF00` — Gray keys it out in his NLE.

## Typography

- **Family:** Montserrat
- **Weight:** Semibold (600)
- **Color:** White `#FFFFFF`
- **Effect:** Drop shadow on all white text (subtle, for legibility against varied A-roll backgrounds Gray will composite onto)
- Built-in font in HyperFrames — no .woff2 files needed.

## Shape Style

- **Strokes:** Thin white (1.5–2px) on most graphical containers
- **Corners:** Rounded — default `border-radius: 24px` for cards/boxes, `border-radius: 999px` for pills
- **Fill:** Transparent or solid white (depending on element)
- **Highlights:** Orange `#F28129` fill or accent

## Drop Shadow Spec (text)

```css
text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
```

## Drop Shadow Spec (containers, when used)

```css
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
```

## Output Defaults

- **Dimensions:** 1080 × 1920 (vertical 9:16)
- **Background:** `#00FF00` chroma green (keyed in Premiere)
- **Format:** MP4 with greenscreen background — switch to transparent ProRes only when graphics have soft edges, glows, or semi-transparent fades

## A-Roll Constraint

All graphics composite OVER Sai's talking-head A-roll. Design rules:
- Respect safe zones — Sai's face is typically centered in the upper-mid frame on vertical shorts
- Use lower or upper third for sustained text/elements
- Full-screen "punch" overlays OK for brief 0.5–1s holds (number reveals, big text hits)
- Picture-in-picture corner placements for sustained graphics (calendars, mockups)

## What NOT to Do

- No drop shadows so heavy they read as bevels
- No gradient backgrounds (H.264 banding on dark gradients)
- No colors outside the white + orange + chroma-green palette
- No "neon" / glow effects that bleed into chroma-key edges
- No serif fonts, no script fonts
