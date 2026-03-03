"""
csv_importer.py
Parses CSV exports from Venmo and bank accounts.
Maps each row to a standard transaction dict ready to append to Google Sheets.

Venmo CSV columns (standard export):
  ID, Datetime, Type, Status, Note, From, To, Amount (total), Amount (fee), Funding Source, Destination, ...

Bank CSV columns vary by bank — we detect headers and handle common patterns.
"""

import csv
import json
import re
import anthropic
from datetime import datetime
from config import ANTHROPIC_API_KEY, CATEGORIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─── Venmo Parser ─────────────────────────────────────────────────────────────

def parse_venmo_csv(filepath):
    """
    Parse a Venmo CSV export and return a list of transaction dicts.
    Only includes completed transactions (skips pending/failed).
    """
    transactions = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        # Venmo CSV has some header/intro rows before the actual data
        lines = f.readlines()

    # Find the row that starts with "ID," — that's the actual header
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("ID,"):
            header_idx = i
            break

    if header_idx is None:
        print("  Could not find Venmo CSV header row. Is this a valid Venmo export?")
        return []

    reader = csv.DictReader(lines[header_idx:])

    for row in reader:
        status = row.get("Status", "").strip()
        if status.lower() != "complete":
            continue

        raw_amount = row.get("Amount (total)", row.get("Amount", "")).strip()
        # Venmo amounts look like "+ $25.00" or "- $25.00"
        is_income = raw_amount.startswith("+")
        amount_str = re.sub(r"[^0-9.]", "", raw_amount)
        if not amount_str:
            continue

        amount = float(amount_str)
        tx_type = "Income" if is_income else "Expense"

        # Parse date
        raw_date = row.get("Datetime", "").strip()
        try:
            dt = datetime.strptime(raw_date[:10], "%Y-%m-%d")
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_str = raw_date[:10]

        note = row.get("Note", "").strip()
        counterparty = row.get("From", "") if is_income else row.get("To", "")
        description = f"{counterparty.strip()} — {note}" if note else counterparty.strip()
        if not description:
            description = "Venmo transaction"

        transactions.append({
            "date": date_str,
            "description": description,
            "source": "Venmo",
            "category": "Income" if is_income else _guess_category(description),
            "amount": amount,
            "type": tx_type,
            "notes": "",
        })

    return transactions


# ─── Bank CSV Parser ───────────────────────────────────────────────────────────

def parse_bank_csv(filepath):
    """
    Parse a bank CSV export and return a list of transaction dicts.
    Handles common column name patterns from major banks.
    """
    transactions = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("  Bank CSV is empty.")
        return []

    headers = [h.strip().lower() for h in rows[0].keys()]

    for row in rows:
        # Normalize keys to lowercase for matching
        r = {k.strip().lower(): v.strip() for k, v in row.items()}

        # Date field
        date_str = _find_field(r, ["date", "transaction date", "posting date", "posted date"])
        if not date_str:
            continue
        date_str = _normalize_date(date_str)

        # Description field
        description = _find_field(r, ["description", "memo", "transaction description", "details", "payee"])
        if not description:
            description = "Bank transaction"

        # Amount field — banks use different patterns
        # Some have separate debit/credit columns, some have a single signed amount
        amount = None
        tx_type = None

        debit = _find_field(r, ["debit", "withdrawal", "amount debit", "debit amount"])
        credit = _find_field(r, ["credit", "deposit", "amount credit", "credit amount"])

        if debit and _parse_amount(debit):
            amount = _parse_amount(debit)
            tx_type = "Expense"
        elif credit and _parse_amount(credit):
            amount = _parse_amount(credit)
            tx_type = "Income"
        else:
            raw = _find_field(r, ["amount", "transaction amount"])
            if raw:
                amount = abs(_parse_amount(raw) or 0)
                tx_type = "Income" if (_parse_amount(raw) or 0) > 0 else "Expense"

        if not amount:
            continue

        category = "Income" if tx_type == "Income" else _guess_category(description)

        transactions.append({
            "date": date_str,
            "description": description,
            "source": "Bank",
            "category": category,
            "amount": amount,
            "type": tx_type,
            "notes": "",
        })

    return transactions


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _find_field(row_dict, possible_keys):
    """Return the first matching value from a normalized row dict."""
    for key in possible_keys:
        if key in row_dict and row_dict[key]:
            return row_dict[key]
    return None


def _parse_amount(value):
    """Parse a dollar amount string to float. Returns None if unparseable."""
    try:
        cleaned = re.sub(r"[^0-9.\-]", "", value)
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _normalize_date(date_str):
    """Try to parse various date formats and return YYYY-MM-DD."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str[:10]  # fallback: return as-is


def _guess_category(description):
    """
    Simple keyword-based category guess.
    Used as a best-effort categorization for CSV imports.
    Claude is used for Gmail receipts which have more context.
    """
    desc = description.lower()

    software_keywords = ["adobe", "capcut", "canva", "notion", "slack", "google", "apple", "microsoft",
                         "spotify", "dropbox", "zoom", "figma", "subscription", "saas", ".com"]
    equipment_keywords = ["amazon", "b&h", "bhphotovideo", "bestbuy", "best buy", "newegg",
                          "adorama", "camera", "microphone", "lens", "tripod", "gear"]
    advertising_keywords = ["meta", "facebook", "instagram", "tiktok", "google ads", "twitter",
                             "x.com", "promoted", "boost", "advertising", "ad spend"]
    contractor_keywords = ["paypal", "upwork", "fiverr", "freelancer", "contractor", "editor",
                           "payment to"]

    for kw in software_keywords:
        if kw in desc:
            return "Software & Subscriptions"
    for kw in equipment_keywords:
        if kw in desc:
            return "Equipment & Gear"
    for kw in advertising_keywords:
        if kw in desc:
            return "Advertising & Marketing"
    for kw in contractor_keywords:
        if kw in desc:
            return "Contractor Payments"

    return "Other"
