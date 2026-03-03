"""
sheets_client.py
Handles all Google Sheets interactions:
  - Authentication
  - Creating/finding worksheet tabs
  - Appending rows to Transactions, Invoices, and Line Items tabs
  - Reading data for the Tax Summary tab
"""

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

from config import (
    GMAIL_CREDENTIALS_PATH,
    GMAIL_TOKEN_PATH,
    GSPREAD_SCOPES,
    GMAIL_SCOPES,
    GOOGLE_SHEET_ID,
    TAB_TRANSACTIONS,
    TAB_INVOICES,
    TAB_LINE_ITEMS,
    TAB_TAX_SUMMARY,
    TRANSACTION_HEADERS,
    INVOICE_HEADERS,
    LINE_ITEM_HEADERS,
    TAX_SUMMARY_HEADERS,
    CATEGORIES,
)

# Combined scopes needed for both Gmail and Sheets in one token
ALL_SCOPES = GMAIL_SCOPES + GSPREAD_SCOPES


def get_credentials():
    """Authenticate and return Google OAuth2 credentials (works for both Gmail and Sheets)."""
    creds = None

    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, ALL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, ALL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def get_sheet():
    """Return the main Google Sheet object."""
    creds = get_credentials()
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID)


def get_or_create_worksheet(sheet, title, headers):
    """Return the worksheet with the given title, creating it with headers if it doesn't exist."""
    try:
        ws = sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws


def setup_sheet():
    """Create all tabs with correct headers. Safe to run multiple times — won't duplicate headers."""
    sheet = get_sheet()

    get_or_create_worksheet(sheet, TAB_TRANSACTIONS, TRANSACTION_HEADERS)
    get_or_create_worksheet(sheet, TAB_INVOICES, INVOICE_HEADERS)
    get_or_create_worksheet(sheet, TAB_LINE_ITEMS, LINE_ITEM_HEADERS)
    ws_tax = get_or_create_worksheet(sheet, TAB_TAX_SUMMARY, TAX_SUMMARY_HEADERS)

    # Populate Tax Summary with category rows + formulas if empty
    existing = ws_tax.get_all_values()
    if len(existing) <= 1:  # only header row
        transactions_tab = TAB_TRANSACTIONS
        # Row index in Transactions tab: Amount=E (col 5), Type=F (col 6), Category=D (col 4)
        rows = []
        for i, cat in enumerate(CATEGORIES[:-1], start=2):  # skip "Income" in expense rows
            formula = (
                f'=SUMPRODUCT((\'{transactions_tab}\'!D2:D1000="{cat}")*'
                f'(\'{transactions_tab}\'!F2:F1000="Expense")*'
                f'(\'{transactions_tab}\'!E2:E1000))'
            )
            rows.append([cat, formula])

        # Income total
        rows.append([
            "Total Income",
            f'=SUMPRODUCT((\'{transactions_tab}\'!F2:F1000="Income")*(\'{transactions_tab}\'!E2:E1000))'
        ])
        # Total expenses
        rows.append([
            "Total Expenses",
            f'=SUMPRODUCT((\'{transactions_tab}\'!F2:F1000="Expense")*(\'{transactions_tab}\'!E2:E1000))'
        ])
        # Net profit
        rows.append(["Net Profit", f"={chr(66)}{len(rows)+1}-{chr(66)}{len(rows)+2}"])

        for row in rows:
            ws_tax.append_row(row)

    print(f"  Sheet setup complete. Tabs: {TAB_TRANSACTIONS}, {TAB_INVOICES}, {TAB_LINE_ITEMS}, {TAB_TAX_SUMMARY}")


def append_transaction(date, description, source, category, amount, tx_type, notes=""):
    """Add one row to the Transactions tab."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    ws.append_row([date, description, source, category, amount, tx_type, notes])


def append_transactions(rows):
    """Add multiple transaction rows at once. Each row is a list matching TRANSACTION_HEADERS."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    for row in rows:
        ws.append_row(row)


def get_next_invoice_number():
    """Return the next invoice number as a zero-padded string like '004'."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_INVOICES)
    all_rows = ws.get_all_values()
    # Subtract 1 for header row; next invoice is count + 1
    count = len(all_rows)  # includes header
    return str(count).zfill(3)


def append_invoice(invoice_num, client, client_email, date, due_date, status, total):
    """Add one row to the Invoices tab."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_INVOICES)
    ws.append_row([invoice_num, client, client_email, date, due_date, status, total])


def append_line_items(invoice_num, line_items):
    """
    Add line item rows to the Invoice Line Items tab.
    line_items: list of dicts with keys: description, hours, rate, flat_fee, subtotal
    """
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_LINE_ITEMS)
    for item in line_items:
        ws.append_row([
            invoice_num,
            item["description"],
            item.get("hours", ""),
            item.get("rate", ""),
            item.get("flat_fee", ""),
            item["subtotal"],
        ])


def update_invoice_status(invoice_num, new_status):
    """Update the Status column for a given invoice number."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_INVOICES)
    cell = ws.find(invoice_num)
    if cell:
        # Status is column 6 (F)
        ws.update_cell(cell.row, 6, new_status)
