"""
main.py
Client CRM + Pipeline Tracker

Commands:
  python main.py setup                    — create Google Sheet (run once)
  python main.py add                      — add a new client (interactive)
  python main.py list                     — list all active clients
  python main.py list --stage "Pitched"   — list clients in a specific stage
  python main.py update <id> <stage>      — move client to new stage
  python main.py remind                   — send weekly Slack reminder now
  python main.py --schedule               — run scheduler (Mondays 9am)
"""

import logging
import os
import sys
import time
import schedule

from crm_sheets import get_sheet, add_client, update_stage, list_clients, get_all_active_clients
from reminder import get_reminders, format_slack_blocks
from slack_notifier import send_reminder
from config import PIPELINE_STAGES

# ─── Logging ────────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "crm.log")
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


def cmd_setup():
    print("  Setting up CRM Google Sheet...")
    get_sheet()
    print("  ✅ CRM sheet ready.")


def cmd_add():
    print("\n" + "=" * 50)
    print("  Add New Client")
    print("=" * 50)
    name = input("\n  Client name: ").strip()
    email = input("  Email: ").strip()
    company = input("  Company (optional): ").strip()
    project = input("  Project type: ").strip()
    budget = input("  Budget ($): ").strip()
    due_date = input("  Due date (YYYY-MM-DD, optional): ").strip()
    notes = input("  Notes (optional): ").strip()

    client_id = add_client(name, email, company, project, budget, due_date, notes)
    print(f"\n  ✅ Client added (ID: {client_id}) — Stage: Lead")
    log.info(f"Added client: {name} (ID: {client_id})")


def cmd_list(stage=None):
    clients = list_clients(stage=stage)
    if not clients:
        print(f"  No clients{' in stage: ' + stage if stage else ''}.")
        return

    header = f"{'ID':<5} {'Name':<20} {'Stage':<16} {'Project':<20} {'Budget':<10} {'Due Date'}"
    print("\n" + header)
    print("-" * len(header))
    for c in clients:
        print(f"{c['id']:<5} {c['name']:<20} {c['stage']:<16} {c['project']:<20} ${c['budget']:<9} {c['due_date']}")


def cmd_update(client_id: str, new_stage: str):
    if new_stage not in PIPELINE_STAGES:
        print(f"  Invalid stage. Choose from: {', '.join(PIPELINE_STAGES)}")
        return
    found = update_stage(client_id, new_stage)
    if found:
        print(f"  ✅ Client {client_id} moved to: {new_stage}")
        log.info(f"Client {client_id} updated to {new_stage}")
    else:
        print(f"  Client ID {client_id} not found.")


def cmd_remind():
    print("  Fetching active clients...")
    clients = get_all_active_clients()
    reminders = get_reminders(clients)
    blocks = format_slack_blocks(reminders, clients)
    send_reminder(blocks)
    print(f"  ✅ Reminder sent ({len(reminders)} follow-up(s) flagged).")
    log.info(f"Weekly reminder sent: {len(reminders)} follow-up(s)")


def run_scheduler():
    log.info("CRM scheduler started. Weekly reminders every Monday at 9:00 AM.")
    schedule.every().monday.at("09:00").do(cmd_remind)
    while True:
        try:
            schedule.run_pending()
        except Exception:
            log.exception("Scheduler error")
        time.sleep(30)


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "setup":
        cmd_setup()
    elif args[0] == "add":
        cmd_add()
    elif args[0] == "list":
        stage_filter = None
        if "--stage" in args:
            idx = args.index("--stage")
            if idx + 1 < len(args):
                stage_filter = args[idx + 1]
        cmd_list(stage=stage_filter)
    elif args[0] == "update" and len(args) >= 3:
        cmd_update(args[1], " ".join(args[2:]))
    elif args[0] == "remind":
        cmd_remind()
    elif args[0] == "--schedule":
        run_scheduler()
    else:
        print(__doc__)
