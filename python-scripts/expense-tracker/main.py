"""
main.py
Personal expense tracker — scans Gmail, extracts expenses via Claude Haiku,
writes expenses.json for the payday checklist to consume.

Run: python main.py
"""

import json
import os
from datetime import date, timezone, datetime

from config import EXPENSES_OUTPUT_PATH, EXCLUDED_VENDORS, CATEGORY_OVERRIDES
from gmail_client import get_gmail_service, fetch_personal_expense_emails
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



def write_expenses_json(expenses, current_month):
    """Write expenses to the payday checklist's expenses.json file."""
    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "month": current_month,
        "expenses": expenses,
    }

    output_path = os.path.normpath(EXPENSES_OUTPUT_PATH)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(expenses)} expense(s) to: {output_path}")


def main():
    today = date.today()
    current_month = f"{today.year}-{today.month:02d}"

    print(f"Expense Tracker — {today.strftime('%B %Y')}")
    print("=" * 40)

    print("\nConnecting to Gmail...")
    service = get_gmail_service()

    print("Searching for expense emails (last 30 days)...")
    emails = fetch_personal_expense_emails(service, days=30)
    print(f"Found {len(emails)} candidate email(s).")

    print("\nExtracting expenses with Claude Haiku...")
    all_expenses = scan_expenses(emails)

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

    print(f"\nTotal for {today.strftime('%B')}: {len(expenses)} expense(s)")

    # Print summary by category
    from collections import defaultdict
    totals = defaultdict(float)
    for e in expenses:
        totals[e["category"]] += e["amount"]
    for cat, total in sorted(totals.items()):
        print(f"  {cat}: ${total:.2f}")

    write_expenses_json(expenses, current_month)


if __name__ == "__main__":
    main()
