"""
main.py
Personal expense tracker — scans Gmail, extracts expenses via Claude Haiku,
writes expenses.json for the payday checklist to consume.

Run: python main.py
"""

import json
import os
import sys
from datetime import date, timezone, datetime

from config import EXPENSES_OUTPUT_PATH, EXCLUDED_VENDORS, CATEGORY_OVERRIDES
from gmail_client import get_gmail_service, fetch_personal_expense_emails, fetch_ej_transfer_emails
from expense_scanner import scan_expenses


def _is_excluded(expense):
    vendor = (expense.get("vendor") or "").lower()
    return any(excl.lower() in vendor for excl in EXCLUDED_VENDORS)


def _apply_category_override(expense):
    vendor = (expense.get("vendor") or "").lower()
    for match, category in CATEGORY_OVERRIDES.items():
        if match.lower() in vendor:
            expense["category"] = category
            return


def dedupe_bank_alerts(expenses):
    """Drop alert expenses that duplicate a vendor receipt OR an already-kept alert
    (same amount, dates within 2 days).

    One purchase can surface three ways: vendor receipt + PrimeSouth Zelle/card
    alert + Rocket Money alert. Merchant strings differ between sources
    ("DOORDASH*NYC" vs "DoorDash" vs "Zelle Money Payme..."), so matching is
    amount + date proximity. Known risk (documented): two genuinely distinct
    same-amount purchases within 2 days that BOTH only exist as alerts collapse
    to one — rare, and Gray can add the missing one manually.
    """
    def _d(s):
        y, m, dd = s.split("-")
        return date(int(y), int(m), int(dd))
    kept = [e for e in expenses if not e.get("is_alert")]
    for a in (e for e in expenses if e.get("is_alert")):
        dup = any(
            k["amount"] == a["amount"] and abs((_d(k["date"]) - _d(a["date"])).days) <= 2
            for k in kept
        )
        if not dup:
            kept.append(a)
    return kept



def write_expenses_json(expenses, current_month, transfers=None):
    """Write expenses + EJ transfers to the payday checklist's expenses.json file."""
    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "month": current_month,
        "expenses": expenses,
        "transfers": transfers or [],
    }

    output_path = os.path.normpath(EXPENSES_OUTPUT_PATH)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(expenses)} expense(s) to: {output_path}")


def main():
    dry_run = "--dry-run" in sys.argv
    today = date.today()
    current_month = f"{today.year}-{today.month:02d}"

    print(f"Expense Tracker — {today.strftime('%B %Y')}")
    print("=" * 40)

    print("\nConnecting to Gmail...")
    service = get_gmail_service()

    print("Searching for expense emails (last 30 days)...")
    emails = fetch_personal_expense_emails(service, days=30)
    print(f"Found {len(emails)} candidate email(s).")

    print("Searching for Edward Jones transfers (last year)...")
    seen_ids = {e["id"] for e in emails}
    ej_emails = [e for e in fetch_ej_transfer_emails(service) if e["id"] not in seen_ids]
    print(f"Found {len(ej_emails)} additional transfer email(s).")
    emails += ej_emails

    print("\nExtracting expenses with Claude Haiku...")
    all_expenses = scan_expenses(emails)

    # Edward Jones transfers (taxes/investing) are allocations, not budget expenses —
    # split them out; the app shows them in the year-to-date Edward Jones card
    current_year = str(today.year)
    transfers = [e for e in all_expenses if e.get("kind") and e["date"].startswith(current_year)]
    all_expenses = [e for e in all_expenses if not e.get("kind")]
    if transfers:
        print(f"  {len(transfers)} Edward Jones transfer(s) this year (tracked separately).")

    # Filter to current month only — Gmail returns 30 days which may include last month
    expenses = [e for e in all_expenses if e["date"].startswith(current_month)]
    filtered = len(all_expenses) - len(expenses)
    if filtered:
        print(f"  Filtered out {filtered} expense(s) from previous month(s).")

    # Exclude rent/non-budget vendors (tracked separately in payday checklist)
    before = len(expenses)
    excluded = [e for e in expenses if _is_excluded(e)]
    expenses = [e for e in expenses if not _is_excluded(e)]
    if excluded:
        print(f"  Excluded {before - len(expenses)} rent/non-budget expense(s):")
        for e in excluded:
            print(f"    - {e['vendor']} ${e['amount']:.2f} ({e['date']})")

    # Apply vendor-specific category overrides
    for e in expenses:
        _apply_category_override(e)

    # Drop bank alerts that duplicate a vendor receipt
    before_dedup = len(expenses)
    expenses = dedupe_bank_alerts(expenses)
    if before_dedup - len(expenses):
        print(f"  Dropped {before_dedup - len(expenses)} bank alert(s) duplicating a receipt.")

    print(f"\nTotal for {today.strftime('%B')}: {len(expenses)} expense(s)")

    # Print summary by category
    from collections import defaultdict
    totals = defaultdict(float)
    for e in expenses:
        totals[e["category"]] += e["amount"]
    for cat, total in sorted(totals.items()):
        print(f"  {cat}: ${total:.2f}")

    if dry_run:
        print("\nDRY RUN — nothing written.")
        return

    write_expenses_json(expenses, current_month, transfers)

    import firestore_writer
    fs_client = firestore_writer.get_client()
    if fs_client:
        created = firestore_writer.write_expenses(expenses + transfers, client=fs_client)
        print(f"Firestore: {created} new record(s) written to {firestore_writer.ROOT}.")
    else:
        print("Firestore: skipped (FIREBASE_SERVICE_ACCOUNT not set).")


if __name__ == "__main__":
    main()
