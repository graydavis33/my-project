# ig-grid-thumbs — branded grid thumbnails for Sai's Instagram

Turns Sai's posted reels into a clean, consistent profile grid.

## The workflow (Claude drives this — Gray just approves)

1. Gray provides source material (any one of these):
   - Plug in the Footage SSD (finals in `08_AI_EDITS/shorts/Batch_NN/`)
   - AirDrop the posted reel videos to the Mac
   - A phone screenshot of the current @saikarra grid (for the diagnosis step)
2. Claude watches each video (video vision), writes 2-3 title options,
   and picks 2-3 candidate frames per video.
3. Claude renders branded covers with `render_thumb.py` and builds a
   before/after grid mockup with `grid_preview.py`.
4. Gray approves → thumbnails land in a synced folder in grid order.
5. Applying to already-posted reels is manual (Instagram doesn't allow
   tools to change covers after posting): IG app → post → Edit →
   Change cover → pick from camera roll. ~3 taps per post.
   For future posts the cover just ships with the posting package.

## Scripts

- `render_thumb.py` — video/frame + title → 1080x1920 cover PNG.
  Title sits inside the center 3:4 zone so it survives the grid crop.
  Montserrat ExtraBold, lowercase-except-names, white + #F28129 accent
  words, soft shadow, optional dark scrim band for legibility.
- `grid_preview.py` — N covers → 3-column IG grid mockup JPG.

## Brand source of truth

`business/sai-karra/editor-onboarding/03-brand-template-spec.md`
Font file reused from `python-scripts/sai-captions/fonts/Montserrat.ttf`.

## Requirements

ffmpeg + Pillow (both already on the Mac; uses sai-captions' venv or
system python3 with Pillow).
