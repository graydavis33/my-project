"""
main.py
CLI entry point for the Invoice & Tax Tracker.

Commands:
  setup-sheet      Create Google Sheet tabs and headers (run once)
  import-csv       Import transactions from a Venmo or Bank CSV file
  scan-receipts    Scan Gmail for expense receipt emails and import them
  scan-payments    Scan Gmail for income payment emails and import them
  scan-all         Run both scan-receipts and scan-payments in one shot (scheduled daily)
  create-invoice   Interactively create + send an invoice

Usage examples:
  python3 main.py setup-sheet
  python3 main.py import-csv --file ~/Downloads/venmo.csv --source venmo
  python3 main.py import-csv --file ~/Downloads/bank.csv --source bank
  python3 main.py scan-receipts
  python3 main.py scan-receipts --days 60
  python3 main.py scan-payments
  python3 main.py scan-payments --days 90
  python3 main.py scan-all
  python3 main.py create-invoice
"""

import argparse
import os
import sys


def cmd_setup_sheet(args):
    from sheets_client import setup_sheet
    print("\n  Setting up Google Sheet...")
    setup_sheet()


def cmd_import_csv(args):
    source = args.source.lower()
    filepath = os.path.expanduser(args.file)

    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        sys.exit(1)

    if source == "venmo":
        from csv_importer import parse_venmo_csv
        print(f"\n  Parsing Venmo CSV: {filepath}")
        transactions = parse_venmo_csv(filepath)
    elif source == "bank":
        from csv_importer import parse_bank_csv
        print(f"\n  Parsing Bank CSV: {filepath}")
        transactions = parse_bank_csv(filepath)
    else:
        print(f"  Unknown source '{source}'. Use: venmo or bank")
        sys.exit(1)

    if not transactions:
        print("  No transactions found.")
        return

    print(f"  Found {len(transactions)} transaction(s). Adding to Google Sheets...")
    from sheets_client import append_transactions
    rows = [
        [
            t["date"],
            t["description"],
            t["source"],
            t["category"],
            t["amount"],
            t["type"],
            t.get("notes", ""),
        ]
        for t in transactions
    ]
    append_transactions(rows)
    print(f"  Done. {len(transactions)} transaction(s) added to the Transactions tab.")


def cmd_scan_receipts(args):
    days = args.days
    print(f"\n  Scanning Gmail for receipts from the last {days} days...")

    from gmail_client import get_gmail_service, fetch_receipt_emails
    from receipt_scanner import scan_receipts
    from sheets_client import append_transactions

    service = get_gmail_service()
    emails = fetch_receipt_emails(service, days=days)

    if not emails:
        print("  No receipt emails found.")
        return

    print(f"  Found {len(emails)} potential receipt email(s). Analyzing with Claude...\n")
    transactions = scan_receipts(emails)

    if not transactions:
        print("  No transactions extracted.")
        return

    rows = [
        [
            t["date"],
            t["description"],
            t["source"],
            t["category"],
            t["amount"],
            t["type"],
            t.get("notes", ""),
        ]
        for t in transactions
    ]
    append_transactions(rows)
    print(f"\n  Done. {len(transactions)} receipt(s) added to the Transactions tab.")


def cmd_scan_payments(args):
    days = args.days
    print(f"\n  Scanning Gmail for payment emails from the last {days} days...")

    from gmail_client import get_gmail_service
    from payment_scanner import fetch_payment_emails, scan_payments
    from sheets_client import append_transactions

    service = get_gmail_service()
    emails = fetch_payment_emails(service, days=days)

    if not emails:
        print("  No payment emails found.")
        return

    print(f"  Found {len(emails)} potential payment email(s). Analyzing with Claude...\n")
    transactions = scan_payments(emails)

    if not transactions:
        print("  No payments detected.")
        return

    rows = [
        [
            t["date"],
            t["description"],
            t["source"],
            t["category"],
            t["amount"],
            t["type"],
            t.get("notes", ""),
        ]
        for t in transactions
    ]
    append_transactions(rows)
    print(f"\n  Done. {len(transactions)} payment(s) added to the Transactions tab.")


def cmd_scan_all(args):
    print("\n═══ Scanning expenses (receipts)...")
    cmd_scan_receipts(args)
    print("\n═══ Scanning income (payments)...")
    cmd_scan_payments(args)
    print("\n  scan-all complete.")


def cmd_create_invoice(args):
    from invoice_generator import create_invoice
    create_invoice()


def main():
    parser = argparse.ArgumentParser(
        prog="python3 main.py",
        description="Invoice & Tax Tracker — by Gray Davis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # setup-sheet
    subparsers.add_parser("setup-sheet", help="Create Google Sheet tabs and headers (run once)")

    # import-csv
    p_csv = subparsers.add_parser("import-csv", help="Import transactions from a CSV file")
    p_csv.add_argument("--file", required=True, help="Path to the CSV file")
    p_csv.add_argument("--source", required=True, choices=["venmo", "bank"], help="CSV source type")

    # scan-receipts
    p_receipts = subparsers.add_parser("scan-receipts", help="Scan Gmail for expense receipt emails")
    p_receipts.add_argument("--days", type=int, default=30, help="How many days back to scan (default: 30)")

    # scan-payments
    p_payments = subparsers.add_parser("scan-payments", help="Scan Gmail for income payment emails")
    p_payments.add_argument("--days", type=int, default=30, help="How many days back to scan (default: 30)")

    # scan-all
    p_all = subparsers.add_parser("scan-all", help="Run both scan-receipts and scan-payments")
    p_all.add_argument("--days", type=int, default=30, help="How many days back to scan (default: 30)")

    # create-invoice
    subparsers.add_parser("create-invoice", help="Create and send a new invoice")

    args = parser.parse_args()

    commands = {
        "setup-sheet": cmd_setup_sheet,
        "import-csv": cmd_import_csv,
        "scan-receipts": cmd_scan_receipts,
        "scan-payments": cmd_scan_payments,
        "scan-all": cmd_scan_all,
        "create-invoice": cmd_create_invoice,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
