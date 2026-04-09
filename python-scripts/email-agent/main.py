"""
main.py
Entry point for the Email Agent.

What it does:
  1. Starts the Slack listener (always running in background)
  2. Every hour from 7am to 8pm, checks Gmail for new emails
  3. Classifies each email with Claude
  4. Writes a draft for emails that need a reply
  5. Sends the draft to Slack with Send / Edit / Skip buttons
  6. Labels each processed email so it's never processed twice

Run this once — it handles its own hourly schedule internally.
"""

import logging
import os
import time
import schedule
from datetime import datetime

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

from gmail_client import (
    get_gmail_service,
    get_or_create_label,
    fetch_unprocessed_emails,
    apply_category_label,
    mark_as_processed,
    archive_email,
    send_email,
)
from classifier import classify_email
from drafter import write_draft
from slack_bot import send_draft_notification, send_followup_alert, start_listener, load_persisted_drafts, register_draft
import followup_tracker
from voice_analyzer import load_voice_profile, build_voice_profile, voice_profile_needs_refresh
from config import (
    PROCESSED_LABEL,
    CATEGORY_NEEDS_REPLY,
    LABEL_NEEDS_REPLY,
    START_HOUR,
    END_HOUR,
)


def _run_payment_scan():
    """Trigger the invoice system's payment scanner after each email check."""
    import subprocess
    import sys as _sys
    invoice_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'invoice-system'))
    # Use invoice-system's own venv Python if it exists (VPS), else fall back to current Python (local)
    _venv_python = os.path.join(invoice_dir, 'venv', 'bin', 'python')
    _python_exe = _venv_python if os.path.exists(_venv_python) else _sys.executable
    try:
        result = subprocess.run(
            [_python_exe, 'main.py', 'scan-payments', '--days', '2'],
            cwd=invoice_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0:
            log.info(f"[Invoice] {output or 'Payment scan complete.'}")
        else:
            log.warning(f"[Invoice] scan-payments error: {output}")
    except Exception:
        log.exception("[Invoice] Payment scan failed")


def run_email_check():
    """Main logic: fetch, classify, draft, notify."""
    log.info("Running email check...")
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'shared'))
        from usage_logger import log_run
        log_run("email-agent")
    except Exception:
        pass

    try:
        service = get_gmail_service()
        label_id = get_or_create_label(service, PROCESSED_LABEL)
        emails = fetch_unprocessed_emails(service, label_id)

        if not emails:
            log.info("No new emails to process.")
        else:
            log.info(f"Found {len(emails)} unprocessed email(s).")

            for email in emails:
                log.info(f"Processing: \"{email['subject']}\" from {email['from']}")

                category, reason = classify_email(email)
                log.info(f"  → Category: {category} | Reason: {reason}")

                # Mark as processed so it won't be picked up again
                mark_as_processed(service, email["id"], label_id)

                if category == CATEGORY_NEEDS_REPLY:
                    # Only needs_reply emails get a category label — skip labeling fyi/ignore
                    apply_category_label(service, email["id"], LABEL_NEEDS_REPLY)
                    draft = write_draft(email)
                    log.info(f"  → Draft written ({len(draft)} chars). Sending to Slack...")

                    # This callback is called when user taps Send in Slack
                    def make_send_callback(e):
                        def send(draft_text):
                            reply_subject = (
                                e["subject"]
                                if e["subject"].startswith("Re:")
                                else f"Re: {e['subject']}"
                            )
                            send_email(
                                service,
                                to=e["from"],
                                subject=reply_subject,
                                body=draft_text,
                                thread_id=e["thread_id"],
                            )
                            log.info(f"Email sent to {e['from']}")
                            followup_tracker.record_sent_reply(e)
                        return send

                    send_draft_notification(email, draft, make_send_callback(email))
                else:
                    archive_email(service, email["id"])
                    log.info(f"  → Archived (no action needed).")

        # Run invoice payment scan every cycle so payments are logged automatically
        log.info("Running invoice payment scan...")
        _run_payment_scan()

        # Check for unanswered replies older than 3 days
        overdue = followup_tracker.check_followups(service)
        if overdue:
            log.info(f"Sending follow-up alert for {len(overdue)} unanswered thread(s).")
            send_followup_alert(overdue)

    except Exception:
        log.exception("Error during email check")


def is_within_active_hours():
    """Only run checks between START_HOUR and END_HOUR."""
    hour = datetime.now().hour
    return START_HOUR <= hour < END_HOUR


def scheduled_check():
    if is_within_active_hours():
        run_email_check()
    else:
        log.info(f"Outside active hours ({START_HOUR}am–{END_HOUR % 12}pm). Skipping.")


def restore_pending_drafts(service):
    """Re-register drafts that were pending when the agent last stopped."""
    persisted = load_persisted_drafts()
    if not persisted:
        return
    log.info(f"Restoring {len(persisted)} pending draft(s) from previous run...")
    for entry in persisted.values():
        email = entry["email"]
        draft = entry["draft"]

        def make_send_callback(e):
            def send(draft_text):
                reply_subject = (
                    e["subject"]
                    if e["subject"].startswith("Re:")
                    else f"Re: {e['subject']}"
                )
                send_email(service, to=e["from"], subject=reply_subject,
                           body=draft_text, thread_id=e["thread_id"])
                log.info(f"Email sent to {e['from']}")
                followup_tracker.record_sent_reply(e)
            return send

        register_draft(email, draft, make_send_callback(email))
    log.info(f"{len(persisted)} draft(s) restored.")


if __name__ == "__main__":
    log.info("=" * 50)
    log.info("Email Agent — Starting up")
    log.info(f"Active hours: {START_HOUR}am – {END_HOUR % 12}pm")
    log.info("Checking every hour for new emails")
    log.info("=" * 50)

    # Build or refresh voice profile — wrapped so a network hiccup can't crash the agent
    try:
        if not load_voice_profile():
            log.info("No voice profile found. Analyzing your sent emails...")
            build_voice_profile()
        elif voice_profile_needs_refresh():
            log.info("Voice profile is >30 days old. Refreshing...")
            build_voice_profile()
        else:
            log.info("Voice profile loaded.")
    except Exception:
        log.exception("Voice profile build failed. Using default style.")

    # Start Slack listener in background
    log.info("Starting Slack listener...")
    try:
        start_listener()
        log.info("Slack listener running.")
    except Exception:
        log.exception("Slack listener failed to start. Continuing without Slack.")

    # Re-register any drafts that were awaiting action when the agent last stopped
    try:
        restore_pending_drafts(get_gmail_service())
    except Exception:
        log.exception("Could not restore pending drafts.")

    # Run once immediately on startup
    if is_within_active_hours():
        run_email_check()

    # Then run every 60 minutes
    schedule.every(60).minutes.do(scheduled_check)

    log.info("Scheduler running. Press Ctrl+C to stop.")
    while True:
        try:
            schedule.run_pending()
        except Exception:
            log.exception("Scheduler error")
        time.sleep(30)
