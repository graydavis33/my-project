"""
main.py
Client Onboarding Automation — full onboarding flow:
  1. Collect client details via CLI
  2. Generate project brief with Claude
  3. Generate contract PDF
  4. Email contract + brief to client
  5. Log to Google Sheets
  6. Notify via Slack

Run:
  cd python-scripts/client-onboarding
  python main.py
"""

import logging
import os

from intake import collect_client_details
from brief_generator import generate_project_brief
from contract_generator import generate_contract_pdf
from onboarding_emailer import get_gmail_service, send_onboarding_email
from sheets_tracker import log_client
from slack_notifier import notify_new_client

# ─── Logging ────────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "onboarding.log")
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


def run_onboarding():
    # Step 1: Collect client details
    details = collect_client_details()
    if not details:
        return

    print("\n  Processing onboarding...")

    # Step 2: Generate project brief
    print("  Generating project brief with Claude...")
    brief = generate_project_brief(details)
    log.info(f"Brief generated for {details['client_name']}")

    # Step 3: Generate contract PDF
    print("  Generating contract PDF...")
    pdf_path = generate_contract_pdf(details)
    print(f"  PDF saved: {pdf_path}")
    log.info(f"Contract PDF: {pdf_path}")

    # Step 4: Send email
    print(f"  Sending contract + brief to {details['client_email']}...")
    try:
        service = get_gmail_service()
        send_onboarding_email(service, details, pdf_path, brief)
        print("  Email sent.")
        log.info(f"Email sent to {details['client_email']}")
    except Exception:
        log.exception("Failed to send onboarding email")
        print("  ⚠️  Email failed — check onboarding.log")

    # Step 5: Log to Google Sheets
    print("  Logging to Google Sheets...")
    try:
        log_client(details)
        print("  Logged.")
        log.info("Logged to Google Sheets")
    except Exception:
        log.exception("Failed to log to Google Sheets")
        print("  ⚠️  Sheets logging failed — check onboarding.log")

    # Step 6: Slack notification
    print("  Sending Slack notification...")
    try:
        notify_new_client(details)
        print("  Slack notification sent.")
        log.info("Slack notification sent")
    except Exception:
        log.exception("Failed to send Slack notification")
        print("  ⚠️  Slack notification failed — check onboarding.log")

    print(f"\n  ✅ {details['client_name']} onboarded successfully!")


if __name__ == "__main__":
    run_onboarding()
