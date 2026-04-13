"""
Photo Organizer — Configuration
"""

# ── Image file types to process ───────────────────────────────────────────────
PHOTO_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif",
    ".tiff", ".tif", ".webp", ".bmp", ".cr2",
    ".cr3", ".nef", ".arw", ".dng", ".orf",
}

# ── Blur detection ─────────────────────────────────────────────────────────────
# Laplacian variance below this value = blurry photo (rejected immediately).
# Lower = more strict (rejects more). Raise this if too many good photos get cut.
BLUR_THRESHOLD = 15.0

# ── Top % to keep per location ─────────────────────────────────────────────────
TOP_PERCENT = 0.25   # 0.25 = keep top 25%

# ── Output folder names ────────────────────────────────────────────────────────
ORGANIZED_FOLDER = "organized"
REJECTED_FOLDER  = "rejected"

# ── Vision-based location grouping ────────────────────────────────────────────
# Uses Claude Haiku to identify the scene/location in each photo visually.
# Results are cached so re-runs are instant and don't cost anything extra.
VISION_CACHE_FILE   = "vision_cache.json"
VISION_MODEL        = "claude-haiku-4-5-20251001"   # cheapest, fast enough
VISION_THUMBNAIL_PX = 512      # resize to this before sending (saves cost)

# After getting all individual descriptions, Claude groups similar ones together
# into clean folder names (e.g. "rocky mountain trail" + "mountain path" → "Mountain Trail")
VISION_GROUP_BATCH  = 80       # send this many descriptions per grouping request

# ── Quality scoring weights (must sum to 1.0) ──────────────────────────────────
# NOTE: Exposure is intentionally excluded — shooter uses RAW and deliberately
# underexposes to recover highlights in post. Penalizing dark shots would cut
# the best frames.
WEIGHT_SHARPNESS  = 0.80   # Is it in focus / sharp?
WEIGHT_CONTRAST   = 0.20   # Does it have tonal range?

# ── Progress & logging ─────────────────────────────────────────────────────────
SHOW_PROGRESS = True
LOG_FILE = "photo-organizer.log"
