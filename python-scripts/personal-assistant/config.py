import os
import sys
from dotenv import load_dotenv

_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(_DIR, ".env"))

_REQUIRED = ["ANTHROPIC_API_KEY", "SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_USER_ID"]
_missing = [k for k in _REQUIRED if not os.getenv(k)]
if _missing:
    print(f"ERROR: Missing required env vars in .env: {', '.join(_missing)}")
    print(f"  Add them to: {os.path.join(_DIR, '.env')}")
    sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SLACK_BOT_TOKEN  = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN  = os.getenv("SLACK_APP_TOKEN")
SLACK_USER_ID    = os.getenv("SLACK_USER_ID")

# Absolute path to python-scripts/ — used by runner.py to find tool folders
_default_base = os.path.normpath(os.path.join(_DIR, ".."))
PA_SCRIPTS_BASE = os.getenv("PA_SCRIPTS_BASE", _default_base)

# Absolute path to the repo root — used by builder_agent.py to resolve relative target dirs
REPO_ROOT = os.path.normpath(os.path.join(_DIR, "../.."))

# Scheduler hours (24h format)
PA_QUEUE_HOUR   = int(os.getenv("PA_QUEUE_HOUR", "2"))   # 2am overnight run
PA_SUMMARY_HOUR = int(os.getenv("PA_SUMMARY_HOUR", "7")) # 7am morning summary

# Max chars of tool output to paste into Slack
PA_MAX_OUTPUT_CHARS = int(os.getenv("PA_MAX_OUTPUT_CHARS", "2000"))
