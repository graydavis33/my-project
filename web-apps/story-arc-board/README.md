# Story-Arc Board

A folder-scoped storyboarding tool for Sai's **long-form**. Built from the 2026-06-14
production review: long-form should be a **story, not a tutorial** — so map the arc
*before* filming the A-roll, and lock the one story + title + thumbnail first.

See `business/social-media/sai/reviews/2026-06-14-production-system-review.md`.

---

## What it does
- You **point it at one specific footage folder** (the week's raw long-form / A-roll).
  It loads only those clips as draggable cards — it does **not** pull arbitrary clips
  from the whole footage library.
- Each clip gets a thumbnail (ffmpeg, auto-rotated so vertical clips show vertical) and
  metadata. If `D:/Sai/.footage-index.sqlite` is mounted, it enriches each clip with its
  `filmed_date`; if the drive isn't connected, it falls back to ffprobe.
- Drag clips (and free-text **plot-point notes**) onto the six **story-arc lanes**:
  Cold Open → Setup → Rising Action → Conflict/Climax → Character Arc/Turn → Resolution.
- Pin the **one story** spine, the **title**, and a **thumbnail** (any clip's ★) at the top —
  the decisions Sai wants locked before the A-roll.
- **Save** the board (to `boards/<slug>.json`) and reload it later.

## Run
```bash
cd web-apps/story-arc-board
python server.py                # http://localhost:4500
python server.py --port 4600    # custom port
```
Then open the URL, paste the week's footage folder path, and click **Load clips**.

## Requirements
- Python 3 (stdlib only — no pip installs)
- `ffmpeg` + `ffprobe` on PATH (already installed on the Windows rig)

## Notes
- `SAI_LIBRARY_ROOT` env var overrides the library root (default `D:/Sai`) used for
  index enrichment. The board works without it — enrichment is optional.
- Thumbnails cache in `.thumbs/` (gitignored). Saved boards live in `boards/` (tracked).
- The footage index (`.footage-index.sqlite`) is opened **read-only** — this tool never
  writes to it.

## Backlog
This is the first system built off the 2026-06-14 review. Others are tracked in
`business/social-media/sai/reviews/SYSTEM-BACKLOG.md`.
