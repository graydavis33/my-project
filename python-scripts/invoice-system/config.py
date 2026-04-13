"""
config.py
Loads all settings from .env and defines shared constants.
"""

import os
import sys
from dotenv import load_dotenv

_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(_DIR, ".env"))

# Validate required env vars before anything else runs
_REQUIRED = ["ANTHROPIC_API_KEY", "GOOGLE_SHEET_ID"]
_missing = [k for k in _REQUIRED if not os.getenv(k)]
if _missing:
    print(f"ERROR: Missing required env vars in .env: {', '.join(_missing)}")
    print(f"  Add them to: {os.path.join(_DIR, '.env')}")
    sys.exit(1)

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Gmail
GMAIL_CREDENTIALS_PATH = os.path.join(_DIR, os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
GMAIL_TOKEN_PATH = os.path.join(_DIR, "token.json")
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GSPREAD_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Invoice output folder
INVOICE_OUTPUT_DIR = os.path.expanduser("~/Desktop/Invoices")

# Your business info (shown on invoices)
YOUR_NAME = "Gray Davis"
YOUR_TITLE = "Social Media Marketing"

# Days until invoice is due after creation
INVOICE_DUE_DAYS = 14

# Tab names in the Google Sheet
TAB_TRANSACTIONS = "Transactions"
TAB_EXPENSES = "Business Expenses"
TAB_TAX_SUMMARY = "Tax Summary"

# Threshold for flagging an income payment as unusual in Notes
LARGE_PAYMENT_THRESHOLD = 5000

# Business expense categories (used for Schedule C tax filing)
CATEGORIES = [
    "Software & Subscriptions",
    "Equipment & Gear",
    "Office",
    "Other",
]

# Slack (optional — for payment notifications)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_PAYMENTS_CHANNEL_ID = os.getenv("SLACK_PAYMENTS_CHANNEL_ID", "")

# Payment sources
SOURCES = ["Venmo", "Bank", "Cash", "Stripe", "Zelle", "Cash App", "QuickBooks", "PayPal", "Direct Deposit"]

# Column headers for each tab
TRANSACTION_HEADERS = ["Date", "Payer", "Source", "Amount", "Notes"]
# Business Expenses tab: [Category | Amount | Date | spacer] per category, then Total column
EXPENSE_HEADERS = []
for _i, _cat in enumerate(CATEGORIES):
    EXPENSE_HEADERS.extend([_cat, "Amount", "Date"])
    if _i < len(CATEGORIES) - 1:
        EXPENSE_HEADERS.append("")   # spacer column between categories
EXPENSE_HEADERS.append("Total")
TAX_SUMMARY_HEADERS = ["Category", "Total"]
