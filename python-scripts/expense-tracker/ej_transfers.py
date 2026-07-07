"""
ej_transfers.py
Deterministic parser for Edward Jones funds-transfer confirmation emails.
These are structured ("To: Sole Proprietor-1 (****8274) ... Requested Amount: $3000"),
so no Haiku call is needed. Account routing:
  Sole Proprietor-* -> kind "tax_transfer"    (Gray's tax set-aside account)
  Single-*          -> kind "invest_transfer" (Gray's investing account)
Transfers are allocations, NOT budget expenses — main.py routes them separately.
"""

import re

_SUBJECT = "funds transfer request has been scheduled"
_SENDER = "edwardjones.com"


def parse_ej_transfer(email):
    if _SENDER not in (email.get("from") or "").lower():
        return None
    if _SUBJECT not in (email.get("subject") or "").lower():
        return None
    body = " ".join((email.get("body") or "").split())

    to = re.search(r"To:\s*([A-Za-z ]+-\d+)\s*\(", body)
    amt = re.search(r"Requested Amount:\s*\$([\d,]+(?:\.\d{1,2})?)", body)
    date = re.search(r"Process Date:\s*(\d{2})/(\d{2})/(\d{4})", body)
    if not (to and amt and date):
        return None

    account = to.group(1).strip()
    low = account.lower()
    if "sole proprietor" in low:
        kind = "tax_transfer"
    elif "single" in low:
        kind = "invest_transfer"
    else:
        return None  # unknown EJ account — don't guess

    return {
        "email_id": email["id"],
        "date": f"{date.group(3)}-{date.group(1)}-{date.group(2)}",
        "vendor": f"Edward Jones ({account})",
        "amount": float(amt.group(1).replace(",", "")),
        "category": "Tax Set-Aside" if kind == "tax_transfer" else "EJ Investing",
        "kind": kind,
    }
