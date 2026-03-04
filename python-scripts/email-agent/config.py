import os
import sys
from dotenv import load_dotenv

# Always load .env from the email-agent folder, regardless of where the script is run from
_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(_DIR, ".env"))

# Validate required env vars before anything else runs
_REQUIRED = ["ANTHROPIC_API_KEY", "SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_USER_ID"]
_missing = [k for k in _REQUIRED if not os.getenv(k)]
if _missing:
    print(f"ERROR: Missing required env vars in .env: {', '.join(_missing)}")
    print(f"  Add them to: {os.path.join(_DIR, '.env')}")
    sys.exit(1)

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")

# Gmail
GMAIL_CREDENTIALS_PATH = os.path.join(_DIR, os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
GMAIL_TOKEN_PATH = os.path.join(_DIR, "token.json")
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",  # needed to apply labels
]

# Agent label applied to emails after processing (prevents duplicates)
PROCESSED_LABEL = "agent-processed"

# Schedule: run every hour from 7am to 8pm
START_HOUR = 7
END_HOUR = 20

# Email categories Claude can assign
CATEGORY_NEEDS_REPLY = "needs_reply"
CATEGORY_FYI_ONLY = "fyi_only"
CATEGORY_IGNORE = "ignore"

# Gmail labels applied per category (shows as nested "Agent/..." labels in Gmail)
LABEL_NEEDS_REPLY = "Agent/Needs Reply"
LABEL_FYI_ONLY = "Agent/FYI Only"
LABEL_IGNORE = "Agent/Ignore"
