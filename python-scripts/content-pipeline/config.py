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

# Obsidian vault path for meeting notes output
OBSIDIAN_SAI_CONVERSATIONS = os.path.expanduser(
    "~/Google Drive/My Drive/Obsidian/Graydient Media/sai-karra/Conversations"
)

# Number of short clips to extract from long-form video
MAX_CLIPS = 5

# Target duration range for short clips (seconds)
CLIP_MIN_SECONDS = 30
CLIP_MAX_SECONDS = 90
