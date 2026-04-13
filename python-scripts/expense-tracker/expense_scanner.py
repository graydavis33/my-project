"""
expense_scanner.py
Uses Claude Haiku to extract personal expense data from Gmail receipt emails.
Processes emails in batches of 5 to minimize API calls.
Deduplicates via .scanned_ids.json so repeat runs don't re-process emails.
"""

import json
import os
import anthropic
from config import ANTHROPIC_API_KEY, PERSONAL_CATEGORIES

_SCANNED_IDS_FILE = os.path.join(os.path.dirname(__file__), ".scanned_ids.json")
_BATCH_SIZE = 5

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM_PROMPT = f"""You are a personal expense tracker. Extract spending data from personal expense emails for Gray Davis.

Given an email, extract:
- date: the transaction date in YYYY-MM-DD format
- vendor: the store or service name (e.g. "Netflix", "Instacart", "Con Edison")
- amount: the total charged as a number only (e.g. 12.99) — no $ sign
- category: one of EXACTLY these five options:
    Groceries   — grocery stores, Instacart, food delivery labeled as groceries
    Dining Out  — restaurants, DoorDash, UberEats, Grubhub, coffee shops
    Utilities   — electricity, gas, internet, phone bill
    Streaming   — Netflix, Spotify, Hulu, Disney+, Apple TV+, YouTube Premium
    Misc        — anything that doesn't clearly fit above

Rules:
- If you cannot find a clear dollar amount, return null
- If this is clearly not a personal purchase receipt, return null
- Return ONLY valid JSON — no other text"""

_BATCH_PROMPT = """Extract personal expense data from each of the following {n} emails.
Return a JSON array of exactly {n} items (one per email, in order).
Each item is either a JSON object, or null if it's not a receipt.

Format for each item:
{{
  "date": "YYYY-MM-DD",
  "vendor": "Vendor Name",
  "amount": 0.00,
  "category": "Category Name"
}}

{emails}

Return ONLY the JSON array — no other text."""

_SINGLE_PROMPT = """Extract personal expense data from this email.

From: {sender}
Subject: {subject}
Date received: {date}

Email body:
{body}

Return ONLY a JSON object:
{{
  "date": "YYYY-MM-DD",
  "vendor": "Vendor Name",
  "amount": 0.00,
  "category": "Category Name"
}}

If this is not a receipt or you can't find the amount, return: null"""


def _load_scanned_ids():
    if os.path.exists(_SCANNED_IDS_FILE):
        try:
            with open(_SCANNED_IDS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_scanned_ids(ids):
    with open(_SCANNED_IDS_FILE, "w") as f:
        json.dump(list(ids), f)


def _format_email_for_batch(i, email):
    return (
        f"--- Email {i} ---\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Date received: {email['date']}\n"
        f"Body:\n{email['body'][:1500]}\n"
    )


def _batch_extract(emails):
    """Send up to _BATCH_SIZE emails in one Claude call. Returns list of dicts or None."""
    n = len(emails)
    emails_text = "\n".join(_format_email_for_batch(i + 1, e) for i, e in enumerate(emails))
    prompt = _BATCH_PROMPT.format(n=n, emails=emails_text)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300 * n,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    try:
        results = json.loads(text)
        if isinstance(results, list) and len(results) == n:
            validated = []
            for r in results:
                validated.append(_validate(r))
            return validated
    except (json.JSONDecodeError, Exception):
        pass

    # Batch parse failed — fall back to individual
    print("    Batch parse failed, falling back to individual extraction...")
    return [_single_extract(e) for e in emails]


def _single_extract(email):
    """Fallback: extract from a single email. Returns a dict or None."""
    prompt = _SINGLE_PROMPT.format(
        sender=email["from"],
        subject=email["subject"],
        date=email["date"],
        body=email["body"][:2000],
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.lower() == "null" or not text:
        return None

    try:
        return _validate(json.loads(text))
    except json.JSONDecodeError:
        return None


def _validate(r):
    """Validate a single extraction result. Returns the dict or None."""
    if r is None or not isinstance(r, dict):
        return None
    if not r.get("amount") or not r.get("vendor") or not r.get("date"):
        return None
    if r.get("category") not in PERSONAL_CATEGORIES:
        r["category"] = "Misc"
    try:
        r["amount"] = round(float(r["amount"]), 2)
    except (ValueError, TypeError):
        return None
    return r


def scan_expenses(emails):
    """
    Extract personal expenses from a list of Gmail emails.
    Skips already-processed emails. Returns list of expense dicts:
    {email_id, date, vendor, amount, category}
    """
    scanned_ids = _load_scanned_ids()
    expenses = []
    newly_scanned = set()

    unscanned = [e for e in emails if e["id"] not in scanned_ids]
    skipped = len(emails) - len(unscanned)
    if skipped:
        print(f"  Skipping {skipped} already-scanned email(s).")

    if not unscanned:
        return expenses

    for batch_start in range(0, len(unscanned), _BATCH_SIZE):
        batch = unscanned[batch_start : batch_start + _BATCH_SIZE]
        print(f"  Processing batch of {len(batch)} email(s) (call {batch_start // _BATCH_SIZE + 1})...")

        results = _batch_extract(batch)

        for email, result in zip(batch, results):
            newly_scanned.add(email["id"])
            if result:
                expense = {
                    "email_id": email["id"],
                    "date": result["date"],
                    "vendor": result["vendor"],
                    "amount": result["amount"],
                    "category": result["category"],
                }
                expenses.append(expense)
                print(f"    + {result['vendor']} ${result['amount']} ({result['category']}) — {result['date']}")
            else:
                print(f"    - {email['subject'][:60]} → not an expense")

    if newly_scanned:
        _save_scanned_ids(scanned_ids | newly_scanned)

    return expenses
