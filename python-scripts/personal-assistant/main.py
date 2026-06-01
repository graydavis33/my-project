"""
main.py
Personal Assistant Agent — entry point.

What it does:
  1. Starts the Slack Socket Mode listener (always-on DM interface)
  2. Registers the 2am overnight queue runner + 7am morning summary
  3. Loops forever, running scheduled jobs every 30 seconds

Run:
  cd python-scripts/personal-assistant
  python main.py
"""

import logging
import os
import time
import schedule

# ─── Logging setup ────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "agent.log")
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

# ─── Imports (after logging so import errors are visible) ─────────────────────
from config import PA_QUEUE_HOUR, PA_SUMMARY_HOUR  # also validates env vars
from slack_bot import start_listener, send_message
from scheduler import register_jobs

# ─── Usage tracking ───────────────────────────────────────────────────────────
try:
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
    from usage_logger import log_run
    log_run("personal-assistant")
except Exception:
    pass


if __name__ == "__main__":
    log.info("=" * 55)
    log.info("Personal Assistant Agent — Starting up")
    log.info(f"Overnight queue runs at: {PA_QUEUE_HOUR:02d}:00")
    log.info(f"Morning summary at:      {PA_SUMMARY_HOUR:02d}:00")
    log.info("=" * 55)

    # Start Slack listener in background thread
    log.info("Starting Slack listener...")
    try:
        start_listener()
        log.info("Slack listener running. DM the bot to get started.")
    except Exception:
        log.exception("Slack listener failed to start — check SLACK_BOT_TOKEN and SLACK_APP_TOKEN.")
        raise

    # Register scheduled jobs (2am queue + 7am summary)
    register_jobs()

    # Let Gray know the agent is live
    try:
        send_message("Personal Assistant is online. DM me anytime — even from your phone.\nType `help` to see what I can do.")
    except Exception:
        log.warning("Could not send startup Slack message.")

    # Main loop — runs scheduled jobs every 30 seconds
    log.info("Scheduler running. Press Ctrl+C to stop.")
    while True:
        try:
            schedule.run_pending()
        except Exception:
            log.exception("Scheduler error")
        time.sleep(30)
