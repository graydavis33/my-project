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

# Obsidian vault path for voice memo transcripts.
# Set OBSIDIAN_VOICE_MEMOS in .env to override per-machine.
_DEFAULT_OBSIDIAN_PATH = "/Users/graydavis28/Library/CloudStorage/GoogleDrive-graydavis33@gmail.com/My Drive/Obsidian/Graydient Media/Voice Memos"
OBSIDIAN_VOICE_MEMOS = os.path.expanduser(
    os.getenv("OBSIDIAN_VOICE_MEMOS", _DEFAULT_OBSIDIAN_PATH)
)

# Number of short clips to extract from long-form video
MAX_CLIPS = 5

# Target duration range for short clips (seconds)
CLIP_MIN_SECONDS = 30
CLIP_MAX_SECONDS = 90
