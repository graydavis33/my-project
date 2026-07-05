# Sai Title Cards — Batch 4 (2026-07-05)

Three brand title cards, Title Case per Gray's ask (brand UPPERCASE rule
overridden intentionally): "Operationalize Kindness" / "Bet On Yourself" /
"Give Back With No Incentive".

## Style (locked Sai brand, from sai-b2v11 DESIGN.md)
- Dark stage card `#34302C → #272320 → #1C1916`, radius 28, drop shadow
- Montserrat ExtraBold 800, white, text shadow (compiler embeds from Google Fonts)
- ONE orange payoff: glass underline `#FFC68A → #F28129 → #D66416` + orange glow

## Animation (simple + smooth)
1. Card rises in (power3.out, 0.65s)
2. Title words stagger up (power2.out, 0.12s apart)
3. Orange underline sweeps left→right (power2.inOut)
4. Subtle idle float on the hold (sine, finite repeats)
6s total, 1080x1920, 60fps.

## Render (title is a variable — new card = new text, no code)
```bash
npx --yes hyperframes@0.6.51 render --fps 60 --format webm \
  --variables '{"title":"Your Title Here","canvasBg":"transparent"}' --output renders/x.webm
ffmpeg -c:v libvpx-vp9 -i renders/x.webm -c:v prores_ks -profile:v 4444 \
  -pix_fmt yuva444p10le -vendor apl0 renders/x_ALPHA.mov
```
ALPHA ProRes only (orange glow + soft shadows fringe on chroma green — locked rule).

## Delivered 2026-07-05
3x `Sai-VFX-Title-*_ALPHA.mov` → `/Volumes/Footage/Sai/06_ASSETS/Visual Effects/Batch 4/`.
Watchable preview: `renders/PREVIEW-all-3-cards.mp4` (all three back-to-back over dark gray).
Variables: title, titleSize 76, cardY 880 (card center), maxCardWidth 940, canvasBg.
