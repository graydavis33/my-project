"""
main.py
Daily Morning Briefing — sends one Slack message at 8am to #morning-briefing with:
  - NYC weather
  - Today's Google Calendar events
  - Emails needing reply (from Email Agent's pending_drafts.json)
  - Outstanding invoices (from Invoice System Google Sheet)
  - Inspirational quote of the day

Run:
  python3 main.py          # send briefing immediately (for testing)
  python3 main.py --schedule  # run scheduler (sends at 8am daily)
"""

import sys
import time
import logging
import os
import schedule
from slack_sdk import WebClient

from config import SLACK_BOT_TOKEN, BRIEFING_CHANNEL_ID
from calendar_summary import get_todays_events
from gmail_summary import get_pending_emails
from sheets_summary import get_outstanding_invoices
from weather_summary import get_weather
from quote_summary import get_daily_quote
from news_summary import get_news_digest
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

    events = get_todays_events()
    log.info(f"  Calendar events today: {len(events)}")

    pending_emails = get_pending_emails()
    log.info(f"  Pending emails: {len(pending_emails)}")

    outstanding_invoices = get_outstanding_invoices()
    log.info(f"  Outstanding invoices: {len(outstanding_invoices)}")

    weather = get_weather()
    log.info(f"  Weather: {weather['temp']}°F {weather['description'] if weather else 'N/A'}")

    quote = get_daily_quote()
    log.info(f"  Quote: {quote['author'] if quote else 'N/A'}")

    news = get_news_digest()
    log.info(f"  Headlines: {len(news.get('top_headlines', []))} | AI digest: {'yes' if news.get('ai_digest') else 'no'}")

    blocks = build_briefing_blocks(events, pending_emails, outstanding_invoices, weather, quote, news)

    slack.chat_postMessage(
        channel=BRIEFING_CHANNEL_ID,
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
        try:
            send_briefing()
        except Exception:
            log.exception("Failed to send morning briefing")
