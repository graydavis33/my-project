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
FOLDER_TEMPLATES      = "00_TEMPLATES"      # Reusable project templates, LUTs, title cards
FOLDER_RAW            = "01_RAW_INCOMING"   # Temporary card dumps — deleted after organize
FOLDER_ORGANIZED      = "02_ORGANIZED"      # AI-sorted output, dated subfolders
FOLDER_PROJECTS       = "03_ACTIVE_PROJECTS" # Active editing projects
FOLDER_DELIVERED      = "04_DELIVERED"       # Finished exports by format, then date
FOLDER_ARCHIVE        = "05_ARCHIVE"         # Retired project files, dated subfolders
FOLDER_FOOTAGE_LIB    = "06_FOOTAGE_LIBRARY" # Reusable footage: category/ → week/
FOLDER_ASSETS         = "07_ASSETS"          # Brand assets, fonts, music, SFX

# Format detection — orientation only (horizontal=long-form, vertical=short-form)
# As of 2026-04-19: long-form is shot 1080p horizontal, short-form is shot vertical.
# Resolution no longer signals format — only orientation does.
FORMAT_LONG_FORM  = "long-form"   # Horizontal (width >= height)
FORMAT_SHORT_FORM = "short-form"  # Vertical   (height > width)

# Content categories — used in ORGANIZED/ (dated) and BROLL_LIBRARY/ (global)
# DESIGN PRINCIPLE: every category has a primary visual question that separates
# it from its neighbors. The model is told to fall back to `miscellaneous` whenever
# two categories could equally apply — Gray reviews those manually.
CATEGORIES = [
    # People — addressing camera
    "interview-solo",
    "interview-duo",
    "walk-and-talk",

    # People — not addressing camera
    "candid-people",
    "reaction-listening",
    "crowd-group",

    # Details / Objects
    "insert-hands",
    "insert-product",
    "insert-food-drink",
    "insert-detail",

    # Screens / Graphics
    "screens-and-text",

    # Environments
    "establishing-exterior",
    "establishing-interior",
    "environment-detail",

    # Movement
    "action-sport-fitness",
    "transit-vehicles",

    # Catch-all — model returns this when uncertain or when 2+ categories tie
    "misc",
]

FRAME_POSITIONS = [0.20, 0.40, 0.60, 0.80]

VIDEO_EXTENSIONS = {".mp4", ".mov", ".MP4", ".MOV"}

# v2 — index + pull
INDEX_DB_NAME    = ".footage-index.sqlite"   # lives at the client library root
PULL_FOLDER_NAME = "_pulls"                  # _pulls/<slug>/ — Premiere-ready hardlink folders
# Roots inside the library that the index scans (ORGANIZED is dated; FOOTAGE_LIBRARY is permanent).
INDEX_SCAN_ROOTS = [FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED]
