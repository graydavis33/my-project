"""
config.py
Load environment variables and constants for the Daily Morning Briefing.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def _require(key):
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val


# Required
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
SLACK_BOT_TOKEN = _require("SLACK_BOT_TOKEN")
SLACK_USER_ID = _require("SLACK_USER_ID")

# Optional — sections are skipped if not set
INVOICE_SHEET_ID = os.getenv("INVOICE_SHEET_ID", "")
ANALYTICS_SHEET_ID = os.getenv("ANALYTICS_SHEET_ID", "")
EMAIL_AGENT_DIR = os.getenv("EMAIL_AGENT_DIR", "")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", os.path.join(os.path.dirname(__file__), "token.json"))

# Your daily top priorities (edit these directly to update your briefing)
DAILY_PRIORITIES = [
    "Follow up on outstanding client proposals",
    "Post one piece of content",
    "Review analytics and adjust strategy",
]
