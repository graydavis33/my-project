# Photo Organizer

## What It Does
- Drop a folder of photos (JPEG, PNG, HEIC, TIFF, WebP, BMP, or RAW — CR2/CR3/NEF/ARW/DNG/ORF)
- Local blur + contrast scoring rejects out-of-focus shots (no API cost)
- Claude Haiku Vision looks at each sharp photo and tags its location/scene
- Groups similar scenes into clean folder names (e.g. "sandy beach" + "tropical beach" → `Beach`)
- Keeps the top 20% per location in `output/organized/`, rest goes to `output/rejected/`
- Originals are never moved or deleted — everything is copied
- Built for a ~1,800-photo Canon CR3 batch; exposure is intentionally ignored because the shooter underexposes on purpose

## Key Files
- `main.py` — orchestration (scan → blur check → vision grouping → copy into folders)
- `extractor.py` — finds photos, loads RAW files via `rawpy`, makes base64 thumbnails for the vision API
- `scorer.py` — local blur detection (Laplacian variance) + contrast scoring, no API calls
- `locator.py` — Claude Haiku vision pass to describe each photo, then a second pass to consolidate descriptions into clean folder names (cached to disk)
- `config.py` — tunables: blur threshold, top-percent, vision model, thumbnail size, scoring weights
- `requirements.txt` — dependencies

## Stack
Python, Claude Haiku Vision (`claude-haiku-4-5-20251001`), Pillow, OpenCV, rawpy, NumPy

## Run
```bash
cd python-scripts/photo-organizer && python main.py /path/to/photos
```

Optional flags:
```bash
python main.py /path/to/photos --output ~/Desktop/sorted
python main.py /path/to/photos --top 30     # keep top 30% per location instead of 20%
```

## Env Vars (.env)
- `ANTHROPIC_API_KEY` — required, powers the Haiku vision calls

## Status
Built. Not in regular workflow yet.

## Notes
- **Cost:** roughly the same shape as footage-organizer — ~$0.001–0.003 per photo (Haiku + 512px thumbnail). A ~1,800-photo batch lands in the $2–5 range.
- **Caching:** `vision_cache.json` is written into the output folder. Re-runs on the same photos are free — no repeat API calls.
- **RAW support:** uses `rawpy` to pull embedded thumbnails when available (fast), falls back to full RAW demosaic if not.
- **Exposure ignored on purpose:** shooter underexposes to protect highlights in post, so dark frames aren't penalized.
- **Blur threshold** lives in `config.py` (`BLUR_THRESHOLD = 15.0`). Raise it if too many keepers get rejected.
- **Top percent default** is 25% in `config.py` but the `--top` flag and the in-code default override to 20% — check `config.py` if the results feel off.
- **Originals are safe** — everything is copied, never moved.
