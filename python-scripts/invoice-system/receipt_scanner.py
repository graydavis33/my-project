"""
receipt_scanner.py
Uses Claude AI to extract transaction data from Gmail receipt emails.
Determines: date, vendor/description, amount, and tax category.

Processes emails in batches of 5 to reduce API calls (~35% fewer tokens).
"""

import json
import os
import anthropic
from config import ANTHROPIC_API_KEY, CATEGORIES

SCANNED_IDS_FILE = os.path.join(os.path.dirname(__file__), '.scanned_receipt_ids.json')
_BATCH_SIZE = 5


def _load_scanned_ids():
    if os.path.exists(SCANNED_IDS_FILE):
        try:
            with open(SCANNED_IDS_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_scanned_ids(ids):
    with open(SCANNED_IDS_FILE, 'w') as f:
        json.dump(list(ids), f)


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a bookkeeping assistant. Your job is to extract transaction data
from receipt and billing emails.

Given an email, extract:
- date: the transaction or billing date (YYYY-MM-DD format)
- description: vendor name + brief description (e.g. "Adobe Creative Cloud - Monthly Subscription")
- amount: the total charged amount as a number (no $ sign, just digits and decimal)
- category: one of these exact options:
  - Software & Subscriptions
  - Equipment & Gear
  - Advertising & Marketing
  - Contractor Payments
  - Other

Rules:
- If you cannot determine the amount with confidence, return null for amount
- If the email is clearly not a receipt or payment confirmation, return null
- Always return valid JSON only — no extra text"""

BATCH_PROMPT = """Extract transaction data from each of the following {n} receipt emails.
Return a JSON array of exactly {n} items (one per email, in order).
Each item is either a JSON object with fields date/description/amount/category, or null if not a receipt.

Format for each item:
{{
  "date": "YYYY-MM-DD",
  "description": "Vendor - Description",
  "amount": 0.00,
  "category": "Category Name"
}}

{emails}

Return ONLY the JSON array — no other text."""

SINGLE_PROMPT = """Extract the transaction data from this receipt email.

From: {sender}
Subject: {subject}
Date received: {date}

Email body:
{body}

Return ONLY a JSON object in this exact format:
{{
  "date": "YYYY-MM-DD",
  "description": "Vendor - Description",
  "amount": 0.00,
  "category": "Category Name"
}}

If this is not a receipt or you can't find the amount, return: null"""


def _format_email_for_batch(i, email):
    return (
        f"--- Email {i} ---\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Date received: {email['date']}\n"
        f"Body:\n{email['body'][:1500]}\n"
    )


def _batch_extract_transactions(emails):
    """
    Send up to _BATCH_SIZE emails in one Claude call.
    Returns a list of result dicts (or None) in the same order as input.
    Falls back to individual extraction if batch parse fails.
    """
    n = len(emails)
    emails_text = "\n".join(_format_email_for_batch(i + 1, e) for i, e in enumerate(emails))
    prompt = BATCH_PROMPT.format(n=n, emails=emails_text)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400 * n,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    try:
        results = json.loads(text)
        if isinstance(results, list) and len(results) == n:
            # Validate each result
            validated = []
            for r in results:
                if r is None or not isinstance(r, dict):
                    validated.append(None)
                    continue
                if not r.get("amount") or not r.get("description"):
                    validated.append(None)
                    continue
                if r.get("category") not in CATEGORIES:
                    r["category"] = "Other"
                validated.append(r)
            return validated
    except (json.JSONDecodeError, Exception):
        pass

    # Batch failed — fall back to individual extraction
    print("    ⚠️  Batch parse failed, falling back to individual extraction...")
    return [_single_extract_transaction(e) for e in emails]


def _single_extract_transaction(email):
    """
    Fallback: extract transaction data from a single email.
    Returns a dict or None.
    """
    prompt = SINGLE_PROMPT.format(
        sender=email["from"],
        subject=email["subject"],
        date=email["date"],
        body=email["body"][:2000],
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    if text.lower() == "null" or not text:
        return None

    try:
        data = json.loads(text)
        if not data or not data.get("amount") or not data.get("description"):
            return None
        if data.get("category") not in CATEGORIES:
            data["category"] = "Other"
        return data
    except json.JSONDecodeError:
        return None


def scan_receipts(emails):
    """
    Run extraction on a list of Gmail emails in batches of 5.
    Skips emails already processed in a previous run (deduplication via ID cache).
    Returns a list of transaction dicts ready to append to Google Sheets.
    Each dict has: date, description, source, category, amount, type, notes
    """
    scanned_ids = _load_scanned_ids()
    transactions = []
    newly_scanned = set()

    # Filter out already-scanned emails
    unscanned = [e for e in emails if e['id'] not in scanned_ids]
    skipped = len(emails) - len(unscanned)
    if skipped:
        print(f"  Skipping {skipped} already-scanned email(s).")

    if not unscanned:
        return transactions

    # Process in batches
    for batch_start in range(0, len(unscanned), _BATCH_SIZE):
        batch = unscanned[batch_start:batch_start + _BATCH_SIZE]
        print(f"  Processing batch of {len(batch)} email(s) (API call {batch_start // _BATCH_SIZE + 1})...")

        results = _batch_extract_transactions(batch)

        for email, result in zip(batch, results):
            newly_scanned.add(email['id'])
            if result:
                transactions.append({
                    "date": result["date"],
                    "description": result["description"],
                    "source": "Gmail",
                    "category": result["category"],
                    "amount": result["amount"],
                    "type": "Expense",
                    "notes": f"Gmail: {email['subject'][:60]}",
                })
                print(f"    ✓ {email['subject'][:50]} → ${result['amount']} | {result['category']}")
            else:
                print(f"    – {email['subject'][:50]} → not a receipt")

    # Persist all newly seen IDs so they're skipped next time
    if newly_scanned:
        _save_scanned_ids(scanned_ids | newly_scanned)

    return transactions
