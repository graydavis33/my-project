"""
config.py
Settings and constants for the personal expense tracker.
"""

import os
import sys
from dotenv import load_dotenv

_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(_DIR, ".env"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print(f"ERROR: Missing ANTHROPIC_API_KEY in {os.path.join(_DIR, '.env')}")
    sys.exit(1)

# Gmail auth
GMAIL_CREDENTIALS_PATH = os.path.join(_DIR, "credentials.json")
GMAIL_TOKEN_PATH = os.path.join(_DIR, "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Output: expenses.json goes into the payday checklist folder
EXPENSES_OUTPUT_PATH = os.path.join(
    _DIR, "..", "..", "web-apps", "payday-checklist", "expenses.json"
)

# Must match the payday checklist's 7 expense categories exactly
# (web-apps/payday-checklist/index.html CATEGORIES — updated 2026-07-06)
PERSONAL_CATEGORIES = ["Groceries", "Dining Out", "Software & Tools", "Utilities", "Investments", "BJJ & Kickboxing", "Misc"]

# Venmo/Zelle/PayPal P2P vendors to exclude from the expense budget.
# These are handled separately in the payday checklist (e.g. rent step), so they
# should NOT count against the monthly budget. Names are matched case-insensitively
# as substrings of the vendor field.
EXCLUDED_VENDORS = [
    "A K",            # rent — roommate share
    "Jodi Ammons",    # rent
    "Ohana Housing",  # rent — landlord
]

# Venmo P2P payees whose category should be forced (Haiku defaults them to Misc
# because the memo is ambiguous). Matched case-insensitively as vendor substring.
CATEGORY_OVERRIDES = {
    "Garrett ODell": "Dining Out",
}

# Bank/money-app transaction alert emails (spend with no vendor receipt email).
# Senders verified against real inbox emails 2026-07-07:
#   alerts.primesouth.com — PrimeSouth Zelle send notifications ("Your $30.00 to
#     Barbershop was sent") + future card alerts once Gray enables them in-app
#   email.rocketmoney.com — Rocket Money watches the PrimeSouth account and mails
#     "Large transaction detected" / "Uncategorized transaction detected"
# The same purchase often appears in BOTH (and sometimes also as a vendor
# receipt) — main.dedupe_bank_alerts collapses them.
ALERT_SENDERS = [
    "alerts.primesouth.com",
    "primesouth.com",
    "email.rocketmoney.com",
]

# Edward Jones transfer confirmations ("Funds Transfer Request Has Been Scheduled").
# Parsed deterministically by ej_transfers.py into tax/investing allocations —
# never budget expenses. Sole Proprietor-* = taxes, Single-* = investing.
TRANSFER_SENDERS = [
    "online-notifications@edwardjones.com",
]
