"""
config.py
Environment variables for Niche Creator Intelligence.
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
SLACK_BOT_TOKEN = _require("SLACK_BOT_TOKEN")
SLACK_USER_ID = _require("SLACK_USER_ID")

# YouTube Data API — reuse credentials from social-media-analytics
YOUTUBE_CREDENTIALS_PATH = os.getenv(
    "YOUTUBE_CREDENTIALS_PATH",
    os.path.join(os.path.dirname(__file__), "..", "social-media-analytics", "client_secret.json")
)
YOUTUBE_TOKEN_PATH = os.getenv(
    "YOUTUBE_TOKEN_PATH",
    os.path.join(os.path.dirname(__file__), "token.json")
)

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# How many recent videos to fetch per creator
VIDEOS_PER_CREATOR = 10

# Cache file to avoid re-fetching data fetched within last 6 days
CACHE_FILE = os.path.join(os.path.dirname(__file__), "creator_cache.json")
CACHE_TTL_DAYS = 6
