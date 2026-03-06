"""
config.py
Environment variables and constants for Client Onboarding Automation.
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

GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", os.path.join(os.path.dirname(__file__), "token.json"))
ONBOARDING_SHEET_ID = os.getenv("ONBOARDING_SHEET_ID", "")  # auto-set on first run

YOUR_NAME = os.getenv("YOUR_NAME", "Gray Davis")
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "")
YOUR_TITLE = os.getenv("YOUR_TITLE", "Freelance Videographer")

OUTPUT_DIR = os.path.expanduser(os.getenv("ONBOARDING_OUTPUT_DIR", "~/Desktop/Onboarding"))

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
GSPREAD_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
