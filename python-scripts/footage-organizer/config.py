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

# v4 b-roll Vision tagging. Opus 4.8 for the initial pass (strong model while
# building the tag data set); drop to claude-haiku-4-5 for cheap incremental
# tagging of new clips later (~5x cheaper). ~$0.015/clip on Opus, ~$0.003 on Haiku.
VISION_TAG_MODEL = "claude-opus-4-8"
VISION_TAG_COST_PER_CLIP = {"claude-opus-4-8": 0.015, "claude-haiku-4-5": 0.003}

# Seed tag vocabularies — a STARTING POINT shown to the Vision model + the
# dashboard, NOT a locked menu. New values are created by typing them in the
# tagging dashboard (persisted to tagger/vocab.json). emotion/action apply only
# when a person (Sai) is in frame; location/objects describe any clip.
EMOTION_TAGS = ["happy", "excited", "stoic", "focused", "stressed",
                "tired", "sad", "angry", "confident", "reflective"]
ACTION_TAGS = ["walking", "talking", "eating", "drinking", "cooking", "working",
               "filming", "driving", "sitting", "exercising", "on-phone", "presenting"]

# Client library roots — set in .env to the root of each client's SSD folder.
# Same physical exFAT drive across machines:
#   Mac:     SAI_LIBRARY_ROOT=/Volumes/Footage/Sai
#   Windows: SAI_LIBRARY_ROOT=D:/Sai
CLIENT_ROOTS = {
    "sai":       os.getenv("SAI_LIBRARY_ROOT", ""),
    "graydient": os.getenv("GRAYDIENT_LIBRARY_ROOT", ""),
}

# Top-level folder names inside each client library root
# Workflow: drop loose footage into 01_ORGANIZED/_INBOX/<date>/ → run organize →
# clips get categorized into 01_ORGANIZED/<category>/<date>/ → after publishing
# video, run --archive <date> → clips move to 05_FOOTAGE_LIBRARY/<category>/W##_*/.
FOLDER_TEMPLATES      = "00_TEMPLATES"      # Reusable project templates, LUTs, title cards
FOLDER_ORGANIZED      = "01_ORGANIZED"      # Holds the _INBOX drop + the categorized output
# Dedicated drop folder for raw, unsorted footage. Lives INSIDE 01_ORGANIZED so the
# inbox and the categorized output never get confused (the old flow dropped loose
# footage straight into 01_ORGANIZED/<date>/, which collided with <category>/<date>/).
# Underscore prefix marks it a helper folder — the index walker skips it, so raw
# inbox clips are never indexed as a bogus "_INBOX" category.
FOLDER_INBOX          = "_INBOX"            # 01_ORGANIZED/_INBOX/<date>/ — drop raw footage here
FOLDER_PROJECTS       = "02_ACTIVE_PROJECTS" # Active editing projects
FOLDER_DELIVERED      = "03_DELIVERED"       # Finished exports by format, then date
# Review-staging area for non-final versions/drafts that someone (Gray, Cy, a
# reviewer) needs to look at before they're discarded. Lives inside 03_DELIVERED.
# Auto-cleaned: items untouched for N+ days are deleted (`drafts-cleanup`), EXCEPT
# project files (.prproj/.aep/.psd/...), which are never auto-deleted. Holds neither
# originals nor finals — only disposable draft exports — so auto-deletion is safe.
FOLDER_DRAFTS         = "drafts"             # 03_DELIVERED/drafts/ — review staging, auto-cleaned
FOLDER_ARCHIVE        = "04_ARCHIVE"         # Retired project files, dated subfolders
FOLDER_FOOTAGE_LIB    = "05_FOOTAGE_LIBRARY" # Reusable footage: category/ → week/
# v4: single consolidated b-roll home inside the footage library. All reusable
# footage flattens into 05_FOOTAGE_LIBRARY/b-roll/<week>/ (original weeks preserved);
# findability comes from index tags (emotion/action/location/object), not from the
# old 17 category folders. Lives beside _BATCHES (interview originals, never b-roll).
FOLDER_BROLL          = "b-roll"             # under 05_FOOTAGE_LIBRARY/
FOLDER_ASSETS         = "06_ASSETS"          # Brand assets, fonts, music, SFX
FOLDER_QUERY_PULLS    = "07_QUERY_PULLS"     # Temp query result folders — deleted after publish
FOLDER_AI_EDITS       = "08_AI_EDITS"        # AI-edited outputs, grouped by content format then source
# AI-edited outputs are filed by CONTENT FORMAT first: 08_AI_EDITS/<format>/<source>/.
#   shorts/   — batch / short-form AI edits (e.g. 08_AI_EDITS/shorts/Batch_03/B3_V## - Title/)
#   longform/ — long-form / episode AI edits (e.g. 08_AI_EDITS/longform/Longform-Pod/)
AI_EDIT_FORMAT_BUCKETS = ["shorts", "longform"]

# Permanent home for batch interview originals — lives INSIDE the footage library
# but runs on its OWN filing system: by Batch_NN/Vid_MM (NOT the category/week
# scheme b-roll uses). Underscore prefix keeps it OUT of the b-roll search index,
# so a finished batch's source takes don't pollute footage searches.
# Final resting place: 05_FOOTAGE_LIBRARY/_BATCHES/Batch_NN/Vid_MM/
FOLDER_BATCHES        = "_BATCHES"           # under 05_FOOTAGE_LIBRARY/

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
PULL_FOLDER_NAME = FOLDER_QUERY_PULLS        # 07_QUERY_PULLS/<slug>/ — Premiere-ready output folders
# Roots inside the library that the index scans (ORGANIZED is dated; FOOTAGE_LIBRARY is permanent).
INDEX_SCAN_ROOTS = [FOLDER_FOOTAGE_LIB, FOLDER_ORGANIZED]
