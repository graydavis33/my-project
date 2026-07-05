# Email Cards — Animated (2026-07-05, Batch 4)

Animated versions of 5 email screenshots (Sharran Srivatsaa x3, Sai + Mark Cuban,
Mark Cuban) with the approved quote-card effect: card fades in, message words
fade in left-to-right, "..." indicator last. Sibling project of
`quote-cards-2026-07-05` (the Sharran "Goodwill" quote).

## How it's built
- Header strips (avatar, name, date, icons) are CROPPED from the real
  screenshots (`assets/g*-header.png`, sources: `~/Downloads/IMG_2009-2013.JPEG`)
  so faces are pixel-identical. They fade in with the card.
- Message text is RETYPED as word spans (SF Pro via system-ui) so each word can
  animate. Layout coords in the `GRAPHICS` config inside index.html.
- Card = native screenshot size (1206 x varying height) centered on 1920x1080.
- `graphic` variable picks the card: g1 Sharran-Holidays, g2 Sharran-CatchUp,
  g3 Sharran-PickOneProblem, g4 SaiCuban-LookForward, g5 Cuban-ThanksForTheTip.

## Rendering
```bash
cd ~/Desktop/my-project/web-apps/hyperframes/email-cards-2026-07-05
# Green-screen MP4
npx --yes hyperframes@0.6.51 render --fps 60 --variables '{"graphic":"g3"}'
# Transparent (webm -> ProRes 4444)
npx --yes hyperframes@0.6.51 render --fps 60 --format webm \
  --variables '{"graphic":"g3","canvasBg":"transparent"}' --output renders/g3.webm
ffmpeg -c:v libvpx-vp9 -i renders/g3.webm -c:v prores_ks -profile:v 4444 \
  -pix_fmt yuva444p10le -vendor apl0 renders/g3_ALPHA.mov
```
Lint warns about `-apple-system` font — harmless on Mac (headless Chrome
resolves system-ui to SF Pro, verified against the originals frame-by-frame).

## Delivered 2026-07-05
All 5 (green MP4 + alpha ProRes each) + the Goodwill quote card →
`/Volumes/Footage/Sai/06_ASSETS/Visual Effects/Batch 4/` as `Sai-VFX-Email-*`.
Green-screen fade caveat: card is semi-transparent over green during the ~1s
fade-in → keyed result can look green-tinted; use the `_ALPHA.mov` if it bugs you.
