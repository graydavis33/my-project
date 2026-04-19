"""
config.py
Environment variables for the Content Repurposing Pipeline.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def _require(key):
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

# Optional — only needed for auto-transcription
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Obsidian vault path for meeting notes output.
# Set OBSIDIAN_SAI_CONVERSATIONS in .env to override (required on Windows, where
# Google Drive for Desktop mounts as a drive letter, e.g. G:/My Drive/...).
_DEFAULT_OBSIDIAN_PATH = "/Users/graydavis28/Library/CloudStorage/GoogleDrive-graydavis33@gmail.com/My Drive/Obsidian/Graydient Media/sai-karra/Conversations"
OBSIDIAN_SAI_CONVERSATIONS = os.path.expanduser(
    os.getenv("OBSIDIAN_SAI_CONVERSATIONS", _DEFAULT_OBSIDIAN_PATH)
)

# Number of short clips to extract from long-form video
MAX_CLIPS = 5

# Target duration range for short clips (seconds)
CLIP_MIN_SECONDS = 30
CLIP_MAX_SECONDS = 90
