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

# Client library roots — set these in .env to the root of each client's SSD folder
# e.g. SAI_LIBRARY_ROOT=/Volumes/MySSD/Sai
CLIENT_ROOTS = {
    "sai":      os.getenv("SAI_LIBRARY_ROOT", ""),
    "graydient": os.getenv("GRAYDIENT_LIBRARY_ROOT", ""),
}

# Format detection — based on resolution/orientation (no API call needed)
FORMAT_LONG_FORM = "long-form"
FORMAT_SHORT_FORM = "short-form"
FORMAT_OTHER = "other"

LONGFORM_WIDTH = 3840
LONGFORM_HEIGHT = 2160

CATEGORIES = [
    "interviews",
    "broll-people",
    "broll-environment",
    "inserts",
    "action",
    "graphics-screens",
    "uncategorized",
]

FRAME_POSITIONS = [0.20, 0.40, 0.60, 0.80]  # % through video to sample

VIDEO_EXTENSIONS = {".mp4", ".mov", ".MP4", ".MOV"}
