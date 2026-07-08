# Logos Title Captions — DESIGN

Three alpha title-card overlays ("NOTION" / "SLACK" / "SCRIBE") that pair with the
`logos-mosaic-row` pixelated-logo B-roll. Words rise from below, one letter at a time,
easy-ease + fade — Gray's brief. Overlaid on footage in Premiere (alpha ProRes).

## Style Prompt
Bold single-word title cards on transparency. Anton caps, white, soft dark drop shadow
for readability over any footage. Motion is the star: per-letter masked rise with a
back-eased settle and blur clearing, then a brand-colored underline sweeps in. A gentle
idle float matches the hovering logos in the companion B-roll.

## Colors
- `#FFFFFF` — the word (all three cards)
- Notion underline — `#FFFFFF` (neutral, matches its black/white brand)
- Slack underline — 4-segment bar `#36C5F0 / #2EB67D / #ECB22E / #E01E5A` (brand colors)
- Scribe underline — `#22E25D` (same green as the Scribe pulse in logos-mosaic-row)
- Shadow — `rgba(0,0,0,0.5)` soft drop shadow (why these are alpha .mov deliverables)

## Typography
- Anton, all caps, 210px, slight tracking (0.02em) — Gray picked it from a 4-font preview

## Motion
- Letters: `yPercent 118 → 0` behind an overflow mask, `back.out(1.35)`, 0.85s,
  stagger 0.065s left→right + opacity fade + blur 9px→0 clearing
- Word container: scale 1.06 → 1.0 settle (power3.out)
- Underline: `scaleX 0 → 1` from the left, `power3.inOut`, after letters land
- Idle: ±6px y float, sine.inOut yoyo (cohesion with the floating logos)
- No exit — Gray cuts the overlay in Premiere

## What NOT to Do
- No backgrounds — pure alpha overlays
- No emojis, no extra decoration beyond the underline
- No crossfade/flicker entrances; letters hard-own their rise
- Don't restyle per card — the three must feel like one set (only the underline changes)
