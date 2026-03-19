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

# Optional: set this in .env once to never need to pass a path argument.
# The tool will ONLY process this folder by default.
FOOTAGE_INBOX = os.getenv("FOOTAGE_INBOX", "")
