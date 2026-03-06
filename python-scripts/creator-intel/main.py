"""
main.py
Niche Creator Intelligence — weekly monitoring of top creators.

Fetches recent videos from configured creators → Claude pattern analysis → Slack report.

Run:
  python main.py              # run immediately (manual / test)
  python main.py --schedule   # run on schedule (Mondays 9:30am)

Edit creators.json to customize which channels to monitor.
"""

import json
import logging
import os
import sys
import time
import schedule

from youtube_fetcher import fetch_all_creators
from analyzer import analyze_creator_data
from slack_reporter import send_report
from config import CACHE_FILE, CACHE_TTL_DAYS

# ─── Logging ────────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "creator_intel.log")
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

_CREATORS_FILE = os.path.join(os.path.dirname(__file__), "creators.json")


def _load_creators():
    with open(_CREATORS_FILE) as f:
        return json.load(f)


def _load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
            if time.time() - data.get("cached_at", 0) < CACHE_TTL_DAYS * 86400:
                return data.get("videos", [])
        except Exception:
            pass
    return None


def _save_cache(videos: list):
    with open(CACHE_FILE, "w") as f:
        json.dump({"cached_at": time.time(), "videos": videos}, f)


def run_report():
    creators = _load_creators()
    log.info(f"Starting creator intel run: {len(creators)} creator(s)")

    # Check cache first
    cached_videos = _load_cache()
    if cached_videos:
        log.info(f"Using cached data ({len(cached_videos)} videos from <{CACHE_TTL_DAYS} days ago)")
        videos = cached_videos
    else:
        log.info("Fetching fresh video data from YouTube...")
        videos = fetch_all_creators(creators)
        if not videos:
            log.warning("No videos fetched — aborting report")
            return
        _save_cache(videos)
        log.info(f"Fetched {len(videos)} videos total")

    log.info("Analyzing with Claude...")
    report = analyze_creator_data(videos)

    log.info("Sending Slack report...")
    send_report(report, len(creators), len(videos))
    log.info("Creator Intel report sent.")


if __name__ == "__main__":
    if "--schedule" in sys.argv:
        log.info("Creator Intel scheduler started. Runs every Monday at 9:30 AM.")
        schedule.every().monday.at("09:30").do(run_report)
        while True:
            try:
                schedule.run_pending()
            except Exception:
                log.exception("Scheduler error")
            time.sleep(30)
    else:
        try:
            run_report()
        except Exception:
            log.exception("Creator intel run failed")
