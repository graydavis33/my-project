"""
config.py
Environment variables for the Transcriber tool.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Only required for --meeting-notes (Claude Haiku writes the notes).
# Left optional at import so a plain transcript runs with NO keys at all.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Optional — Whisper API fallback if local Whisper isn't installed.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Obsidian vault path for voice memo transcripts.
# Set OBSIDIAN_VOICE_MEMOS in .env to override per-machine (required on Windows).
_DEFAULT_OBSIDIAN_PATH = "/Users/graydavis28/Library/CloudStorage/GoogleDrive-graydavis33@gmail.com/My Drive/Obsidian/Graydient Media/Voice Memos"
OBSIDIAN_VOICE_MEMOS = os.path.expanduser(
    os.getenv("OBSIDIAN_VOICE_MEMOS", _DEFAULT_OBSIDIAN_PATH)
)
