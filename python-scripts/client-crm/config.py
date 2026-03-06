"""
config.py
Environment variables and pipeline stage configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def _require(key):
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val


SLACK_BOT_TOKEN = _require("SLACK_BOT_TOKEN")
SLACK_USER_ID = _require("SLACK_USER_ID")

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", os.path.join(os.path.dirname(__file__), "token.json"))
CRM_SHEET_ID = os.getenv("CRM_SHEET_ID", "")

# Pipeline stages in order
PIPELINE_STAGES = [
    "Lead",
    "Pitched",
    "Contracted",
    "In Production",
    "Delivered",
    "Paid",
]

# Days before auto-reminder fires per stage (0 = no reminder)
STAGE_REMINDER_DAYS = {
    "Lead":           3,   # remind if no update in 3 days
    "Pitched":        7,   # remind if no update in 7 days
    "Contracted":     0,   # remind based on due date instead
    "In Production":  0,   # remind based on due date
    "Delivered":      7,   # remind every 7 days until paid
    "Paid":           0,   # no reminder needed
}

GSPREAD_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
