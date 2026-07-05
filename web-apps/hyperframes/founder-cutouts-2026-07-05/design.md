# Founder Cutouts — Mark Cuban / Sharran Srivatsaa / Justin Kan (2026-07-05)

Rotoscoped (background-removed) medium-shot cutouts of the three founders,
staged in a HyperFrames comp on chroma green. Built for Batch 4 email/quote
content — drop over Sai's talking head or key/composite as needed.

## Assets (`assets/`)
- `mark-cuban.png` (1121x1400) — Gage Skidmore photo, Wikimedia CC BY-SA
- `sharran-srivatsaa.png` (874x1372) — sharran.com official press kit (waist-up, gesturing)
- `justin-kan.png` (1236x1400) — TechCrunch Disrupt 2019, Flickr CC BY, chest-up crop

Full-res originals + masters in the session scratchpad (temporary);
re-create via `npx hyperframes remove-background <photo>.jpg -o cutout.png`
(u2net_human_seg). Kan needed extra cleanup: white couch pixels removed from
the bottom band with a bright+desaturated filter (skin stays, couch goes).

## Composition
- 1920x1080, 8s, chroma green canvas (`canvasBg` variable, `transparent` for alpha renders)
- Three cutouts bottom-aligned, evenly spaced; each rises in with a soft fade
- Variables: `cutoutHeight` (760), per-person `show*` toggles, `riseStart`, `riseStagger`
- To render one person alone: `--variables '{"showCuban":true,"showSharran":false,"showKan":false}'`

## Render
```bash
npx --yes hyperframes@0.6.51 render --fps 60                       # green MP4
npx --yes hyperframes@0.6.51 render --fps 60 --format webm \
  --variables '{"canvasBg":"transparent"}'                         # alpha (convert to ProRes via ffmpeg, see email-cards design.md)
```
