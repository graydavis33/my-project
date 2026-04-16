import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def _require(key):
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required env var: {key}  (check your .env file)"
        )
    return val


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

MODEL = "claude-haiku-4-5-20251001"

# Client library roots — set in .env to the root of each client's SSD folder
# e.g. SAI_LIBRARY_ROOT=/Volumes/SSD/Sai
CLIENT_ROOTS = {
    "sai":       os.getenv("SAI_LIBRARY_ROOT", ""),
    "graydient": os.getenv("GRAYDIENT_LIBRARY_ROOT", ""),
}

# Top-level folder names inside each client library root
FOLDER_RAW       = "RAW"        # Temporary card dumps, dated subfolders
FOLDER_ORGANIZED = "ORGANIZED"  # AI-sorted output, dated subfolders
FOLDER_PROJECTS  = "PROJECTS"   # Active editing projects
FOLDER_ARCHIVE   = "ARCHIVE"    # Global reusable library, no dates, by category
FOLDER_PUBLISH   = "PUBLISH"    # Completed exports ready to post

# Format detection — based on resolution (no API call needed)
FORMAT_LONG_FORM  = "long-form"   # 4K horizontal  (3840x2160)
FORMAT_SHORT_FORM = "short-form"  # Vertical        (height > width)
FORMAT_OTHER      = "other"       # Everything else

LONGFORM_WIDTH  = 3840
LONGFORM_HEIGHT = 2160

# Content categories — used in ORGANIZED/ (dated) and ARCHIVE/ (global)
CATEGORIES = [
    "interviews",           # Person speaking directly to camera, talking-head
    "broll-people",         # People in candid activity, walking, working, lifestyle
    "broll-inserts",        # Close-ups of hands, objects, food, gear, product details
    "broll-environment",    # Landscapes, architecture, interiors (no people focus)
    "establishing-shots",   # Wide shots setting a location or scene context
    "location-shots",       # Specific recognizable location footage (NYC street, office, etc.)
    "action-shots",         # Fast movement, sports, vehicles, dynamic sequences
    "broll-office",         # Office interiors, desk setups, workspace footage
    "screen-recordings",    # Monitor/phone screens, dashboards, UI, software demos
    "duo-shots",            # Two people in frame together
    "reaction-shots",       # Reactions, listening shots, over-the-shoulder
    "product-shots",        # Products, gear, equipment on display
    "miscellaneous",        # Anything that doesn't fit above
]

FRAME_POSITIONS = [0.20, 0.40, 0.60, 0.80]

VIDEO_EXTENSIONS = {".mp4", ".mov", ".MP4", ".MOV"}
