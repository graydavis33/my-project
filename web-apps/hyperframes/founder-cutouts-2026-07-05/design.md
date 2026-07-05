# Founder Photos — Mark Cuban / Sharran Srivatsaa / Justin Kan (2026-07-05)

Original medium-shot photos of the three founders, staged in a HyperFrames
comp. Gray's call 2026-07-05: keep the ORIGINAL photos (no roto cutouts) —
he handles any cutting out himself in his own tools.

## Assets (`assets/`) — full-res originals
- `mark-cuban.jpg` (2196x2874) — Gage Skidmore photo, Wikimedia CC BY-SA, chest-up, dark blue backdrop
- `sharran-srivatsaa.jpg` (2560x1706) — sharran.com official press kit, waist-up on stage gesturing
- `justin-kan.jpg` (1280x1920) — pro studio portrait (Fortune headshot), orange backdrop, chest-up, front-facing. Replaced the TechCrunch Disrupt 2019 stage shot 2026-07-05 per Gray ("better picture").

If cutouts are ever wanted again: `npx hyperframes remove-background <photo> -o cutout.png`
(u2net_human_seg; Kan's white couch needs a bright+desaturated pixel cleanup in the bottom band).

## Composition
- 1920x1080, 8s, chroma green canvas (`canvasBg` variable)
- Photos bottom-aligned in a row, each rises in with a soft fade
- Variables: `cutoutHeight` (photo height, 760), per-person `show*` toggles, `riseStart`, `riseStagger`
