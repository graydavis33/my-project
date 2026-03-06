"""
main.py
Daily Morning Briefing — sends one Slack DM at 8am with:
  - Emails needing reply (from Email Agent's pending_drafts.json)
  - Outstanding invoices (from Invoice System Google Sheet)
  - Top video this week (from Analytics Google Sheet)
  - Top 3 priorities for the day (configured in config.py)

Run:
  python main.py          # send briefing immediately (for testing)
  python main.py --schedule  # run scheduler (sends at 8am daily)
"""

import sys
import time
import logging
import os
import schedule
from slack_sdk import WebClient

from config import SLACK_BOT_TOKEN, SLACK_USER_ID
from gmail_summary import get_pending_emails
from sheets_summary import get_outstanding_invoices, get_top_video_this_week
from briefing import build_briefing_blocks

# ─── Logging ────────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "briefing.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

slack = WebClient(token=SLACK_BOT_TOKEN)


def send_briefing():
    """Collect all data and send the morning briefing to Slack."""
    log.info("Assembling morning briefing...")

    pending_emails = get_pending_emails()
    log.info(f"  Pending emails: {len(pending_emails)}")

    outstanding_invoices = get_outstanding_invoices()
    log.info(f"  Outstanding invoices: {len(outstanding_invoices)}")

    top_video = get_top_video_this_week()
    log.info(f"  Top video: {top_video['title'] if top_video else 'N/A'}")

    blocks = build_briefing_blocks(pending_emails, outstanding_invoices, top_video)

    slack.chat_postMessage(
        channel=SLACK_USER_ID,
        blocks=blocks,
        text="☀️ Good morning! Here's your daily briefing.",
    )
    log.info("Morning briefing sent.")


if __name__ == "__main__":
    scheduled = "--schedule" in sys.argv

    if scheduled:
        log.info("Morning Briefing scheduler started. Will send at 8:00 AM daily.")
        schedule.every().day.at("08:00").do(send_briefing)
        while True:
            try:
                schedule.run_pending()
            except Exception:
                log.exception("Scheduler error")
            time.sleep(30)
    else:
        # Send immediately (manual run or test)
        try:
            send_briefing()
        except Exception:
            log.exception("Failed to send morning briefing")
