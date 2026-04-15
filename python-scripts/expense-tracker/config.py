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

# Must match the payday checklist's 5 expense categories exactly
PERSONAL_CATEGORIES = ["Groceries", "Dining Out", "Software & Tools", "Streaming", "Utilities", "Transport", "Health & Wellness", "Shopping", "Misc"]

# Venmo/Zelle/PayPal P2P vendors to exclude from the expense budget.
# These are handled separately in the payday checklist (e.g. rent step), so they
# should NOT count against the monthly budget. Names are matched case-insensitively
# as substrings of the vendor field.
EXCLUDED_VENDORS = [
    "A K",            # rent — roommate share
    "Jodi Ammons",    # rent
    "Ohana Housing",  # rent — landlord
]
