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

import time
import schedule
from datetime import datetime

from gmail_client import (
    get_gmail_service,
    get_or_create_label,
    fetch_unprocessed_emails,
    apply_category_label,
    mark_as_processed,
    send_email,
)
from classifier import classify_email
from drafter import write_draft
from slack_bot import send_draft_notification, start_listener
from voice_analyzer import load_voice_profile, build_voice_profile
from config import (
    PROCESSED_LABEL,
    CATEGORY_NEEDS_REPLY,
    CATEGORY_FYI_ONLY,
    CATEGORY_IGNORE,
    LABEL_NEEDS_REPLY,
    LABEL_FYI_ONLY,
    LABEL_IGNORE,
    START_HOUR,
    END_HOUR,
)


def run_email_check():
    """Main logic: fetch, classify, draft, notify."""
    now = datetime.now()
    print(f"\n[{now.strftime('%Y-%m-%d %H:%M')}] Running email check...")

    try:
        service = get_gmail_service()
        label_id = get_or_create_label(service, PROCESSED_LABEL)
        emails = fetch_unprocessed_emails(service, label_id)

        if not emails:
            print("  No new emails to process.")
            return

        print(f"  Found {len(emails)} unprocessed email(s).")

        for email in emails:
            print(f"  Processing: \"{email['subject']}\" from {email['from']}")

            category = classify_email(email)
            print(f"    → Category: {category}")

            # Apply category label so email is organized in Gmail
            category_label_map = {
                CATEGORY_NEEDS_REPLY: LABEL_NEEDS_REPLY,
                CATEGORY_FYI_ONLY: LABEL_FYI_ONLY,
                CATEGORY_IGNORE: LABEL_IGNORE,
            }
            if category in category_label_map:
                apply_category_label(service, email["id"], category_label_map[category])

            # Mark as processed so it won't be picked up again
            mark_as_processed(service, email["id"], label_id)

            if category == CATEGORY_NEEDS_REPLY:
                draft = write_draft(email)
                print(f"    → Draft written ({len(draft)} chars). Sending to Slack...")

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
                        print(f"  ✅ Email sent to {e['from']}")
                    return send

                send_draft_notification(email, draft, make_send_callback(email))
            else:
                print(f"    → No action needed.")

    except Exception as e:
        print(f"  ❌ Error during email check: {e}")


def is_within_active_hours():
    """Only run checks between START_HOUR and END_HOUR."""
    hour = datetime.now().hour
    return START_HOUR <= hour < END_HOUR


def scheduled_check():
    if is_within_active_hours():
        run_email_check()
    else:
        print(f"[{datetime.now().strftime('%H:%M')}] Outside active hours ({START_HOUR}am–{END_HOUR % 12}pm). Skipping.")


if __name__ == "__main__":
    print("=" * 50)
    print("  Email Agent — Starting up")
    print(f"  Active hours: {START_HOUR}am – {END_HOUR % 12}pm")
    print(f"  Checking every hour for new emails")
    print("=" * 50)

    # Build voice profile on first run (skipped if already exists)
    if not load_voice_profile():
        print("\n  No voice profile found. Analyzing your sent emails...")
        build_voice_profile()
    else:
        print("\n  ✅ Voice profile loaded.")

    # Start Slack listener in background
    print("\n  Starting Slack listener...")
    start_listener()
    print("  ✅ Slack listener running.\n")

    # Run once immediately on startup
    if is_within_active_hours():
        run_email_check()

    # Then run every hour
    schedule.every().hour.do(scheduled_check)

    print("\n  Scheduler running. Press Ctrl+C to stop.\n")
    while True:
        schedule.run_pending()
        time.sleep(30)
