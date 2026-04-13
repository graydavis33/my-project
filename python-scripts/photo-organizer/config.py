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
BLUR_THRESHOLD = 80.0

# ── Top % to keep per location ─────────────────────────────────────────────────
TOP_PERCENT = 0.20   # 0.20 = keep top 20%

# ── GPS clustering ─────────────────────────────────────────────────────────────
# Photos within this many meters of each other = same location cluster
CLUSTER_RADIUS_METERS = 500

# Minimum photos needed to form a named location group.
# Lone photos that don't cluster go into "Uncategorized"
MIN_CLUSTER_SIZE = 1

# ── Output folder names ────────────────────────────────────────────────────────
ORGANIZED_FOLDER = "organized"
REJECTED_FOLDER  = "rejected"

# ── Reverse geocoding ──────────────────────────────────────────────────────────
# Nominatim (OpenStreetMap) — free, no API key needed.
# Rate limit: 1 request per second (handled automatically).
GEOCODE_USER_AGENT  = "photo-organizer-gray"
GEOCODE_CACHE_FILE  = "geocode_cache.json"

# ── Quality scoring weights (must sum to 1.0) ──────────────────────────────────
WEIGHT_SHARPNESS  = 0.60   # Most important — is it in focus?
WEIGHT_EXPOSURE   = 0.25   # Is it properly lit (not too dark / too bright)?
WEIGHT_CONTRAST   = 0.15   # Does it have tonal range?

# ── Progress & logging ─────────────────────────────────────────────────────────
SHOW_PROGRESS = True
LOG_FILE = "photo-organizer.log"
