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
TAB_INVOICES = "Invoices"
TAB_LINE_ITEMS = "Invoice Line Items"
TAB_TAX_SUMMARY = "Tax Summary"

# Transaction categories
CATEGORIES = [
    "Software & Subscriptions",
    "Equipment & Gear",
    "Advertising & Marketing",
    "Contractor Payments",
    "Other",
    "Income",
]

# Transaction sources
SOURCES = ["Venmo", "Bank", "Gmail", "Cash"]

# Column headers for each tab
TRANSACTION_HEADERS = ["Date", "Description", "Source", "Category", "Amount", "Type", "Notes"]
INVOICE_HEADERS = ["Invoice #", "Client", "Client Email", "Date", "Due Date", "Status", "Total"]
LINE_ITEM_HEADERS = ["Invoice #", "Description", "Hours", "Hourly Rate", "Flat Fee", "Subtotal"]
TAX_SUMMARY_HEADERS = ["Category", "Total"]
