"""
scheduler.py
Registers the two recurring jobs:
  1. PA_QUEUE_HOUR (default 2am) — process the overnight queue
  2. PA_SUMMARY_HOUR (default 7am) — send a morning summary

Called once from main.py at startup.
"""

import logging
import schedule
import time
from datetime import datetime

from config import PA_QUEUE_HOUR, PA_SUMMARY_HOUR
from slack_bot import send_message
from task_queue import pop_all_pending, mark_done, list_pending, format_queue_list
from runner import run_tool, format_result

log = logging.getLogger(__name__)


def process_overnight_queue():
    """
    Run every task in the queue sequentially.
    Sends a Slack report when all tasks are done.
    """
    tasks = pop_all_pending()
    if not tasks:
        log.info("Overnight queue is empty — nothing to run.")
        return

    log.info(f"Overnight run starting. {len(tasks)} task(s) in queue.")
    send_message(f"Starting overnight run — {len(tasks)} task(s) queued...")

    results = []
    for task in tasks:
        tool = task["tool"]
        args = task["args"]
        log.info(f"Running queued task: {tool} {args}")
        result = run_tool(tool, args)
        mark_done(tool, result["success"])
        results.append((tool, result))

    # Build consolidated Slack report
    lines = [f"Overnight run complete — {len(tasks)} task(s) finished.\n"]
    for tool, result in results:
        lines.append(format_result(tool, result))
        lines.append("")  # blank line between tools

    send_message("\n".join(lines))
    log.info("Overnight run complete.")


def send_morning_summary():
    """
    Send a morning summary: what ran overnight + anything still queued.
    """
    pending = list_pending()
    lines = [f"Good morning. Here's your agent status:\n"]

    if pending:
        lines.append(format_queue_list())
    else:
        lines.append("Queue is empty — nothing scheduled for tonight yet.")

    lines.append("\nType `help` to see what I can run for you today.")
    send_message("\n".join(lines))
    log.info("Morning summary sent.")


def register_jobs():
    """Register all scheduled jobs. Call once from main.py."""
    queue_time = f"{PA_QUEUE_HOUR:02d}:00"
    summary_time = f"{PA_SUMMARY_HOUR:02d}:00"

    schedule.every().day.at(queue_time).do(process_overnight_queue)
    schedule.every().day.at(summary_time).do(send_morning_summary)

    log.info(f"Scheduled: overnight queue run at {queue_time}, morning summary at {summary_time}")
