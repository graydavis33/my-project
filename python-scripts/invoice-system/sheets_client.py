"""
sheets_client.py
Handles all Google Sheets interactions:
  - Authentication
  - Creating/finding worksheet tabs
  - Appending rows to Transactions and Business Expenses tabs
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
    TAB_EXPENSES,
    TAB_TAX_SUMMARY,
    TRANSACTION_HEADERS,
    EXPENSE_HEADERS,
    TAX_SUMMARY_HEADERS,
    CATEGORIES,
)

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


def _auto_resize(spreadsheet, ws):
    """Auto-fit all columns to match content width."""
    spreadsheet.batch_update({
        "requests": [{
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": ws.id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": ws.col_count,
                }
            }
        }]
    })


def _auto_resize_all(spreadsheet):
    """Auto-fit all columns on every worksheet in the spreadsheet."""
    for ws in spreadsheet.worksheets():
        _auto_resize(spreadsheet, ws)


def _format_currency_column(spreadsheet, ws, col_index=3):
    """Format the Amount column as $ currency (col_index is 0-based, default=3 for column D)."""
    spreadsheet.batch_update({
        "requests": [{
            "repeatCell": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": 1,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY",
                            "pattern": "$#,##0.00",
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        }]
    })


def _add_totals_row(spreadsheet, ws):
    """Insert a bold TOTAL row at row 2 if not already present. Data lives in rows 3+."""
    row2 = ws.row_values(2)
    if row2 and row2[0] == "TOTAL":
        return  # already set up
    ws.insert_row(["TOTAL", "", "", "=SUM(D3:D1000)", ""], index=2)
    spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 26,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    }]})


def _freeze_rows(spreadsheet, ws, count=2):
    """Freeze the top N rows so header + totals stay visible while scrolling."""
    spreadsheet.batch_update({"requests": [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": ws.id,
                "gridProperties": {"frozenRowCount": count},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    }]})


def _expand_sheet_dimensions(spreadsheet, ws, rows=1000, cols=26):
    """Ensure a worksheet has at least the given number of rows and columns."""
    requests = []
    if ws.row_count < rows:
        requests.append({"appendDimension": {"sheetId": ws.id, "dimension": "ROWS", "length": rows - ws.row_count}})
    if ws.col_count < cols:
        requests.append({"appendDimension": {"sheetId": ws.id, "dimension": "COLUMNS", "length": cols - ws.col_count}})
    if requests:
        spreadsheet.batch_update({"requests": requests})


def get_or_create_worksheet(sheet, title, headers):
    """Return the worksheet with the given title, creating it with headers if it doesn't exist."""
    try:
        ws = sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows=1000, cols=26)
        ws.append_row(headers)
    return ws


def setup_sheet():
    """
    Create Transactions, Business Expenses, and Tax Summary tabs with correct headers.
    Deletes Invoices and Invoice Line Items tabs if they exist (legacy cleanup).
    Safe to run multiple times — won't duplicate headers.
    """
    sheet = get_sheet()

    # Remove legacy tabs if present
    for legacy_tab in ["Invoices", "Invoice Line Items"]:
        try:
            ws = sheet.worksheet(legacy_tab)
            sheet.del_worksheet(ws)
            print(f"  Removed legacy tab: {legacy_tab}")
        except gspread.WorksheetNotFound:
            pass

    # Reset Transactions tab if headers are outdated (clears old-format data)
    try:
        ws_existing = sheet.worksheet(TAB_TRANSACTIONS)
        if ws_existing.row_values(1) != TRANSACTION_HEADERS:
            sheet.del_worksheet(ws_existing)
            print("  Reset Transactions tab (headers updated, old data cleared)")
    except gspread.WorksheetNotFound:
        pass
    ws_tx = get_or_create_worksheet(sheet, TAB_TRANSACTIONS, TRANSACTION_HEADERS)
    ws_exp = get_or_create_worksheet(sheet, TAB_EXPENSES, EXPENSE_HEADERS)
    ws_tax = get_or_create_worksheet(sheet, TAB_TAX_SUMMARY, TAX_SUMMARY_HEADERS)

    # Expand all tabs to full spreadsheet dimensions (1000 rows x 26 cols)
    for ws in [ws_tx, ws_exp, ws_tax]:
        _expand_sheet_dimensions(sheet, ws)

    # Add pinned TOTAL row (row 2) and freeze header + totals on data tabs
    for ws in [ws_tx, ws_exp]:
        _add_totals_row(sheet, ws)
        _freeze_rows(sheet, ws, count=2)

    # Always rebuild Tax Summary formulas (start at row 3 to skip the TOTAL row)
    ws_tax.clear()
    ws_tax.append_row(TAX_SUMMARY_HEADERS)
    if True:
        tx = TAB_TRANSACTIONS
        exp = TAB_EXPENSES

        rows = []

        # Total Income — sum of Amount column (D) in Transactions (row 3+ skips TOTAL row)
        rows.append(["Total Income", f"=SUM('{tx}'!D3:D1000)"])

        # Expense categories — SUMPRODUCT by Category column (C) in Business Expenses
        for cat in CATEGORIES:
            formula = (
                f"=SUMPRODUCT(('{exp}'!C3:C1000=\"{cat}\")*"
                f"('{exp}'!D3:D1000))"
            )
            rows.append([cat, formula])

        # Total Expenses — sum of Amount column (D) in Business Expenses
        rows.append(["Total Expenses", f"=SUM('{exp}'!D3:D1000)"])

        # Net Profit = Total Income - Total Expenses
        income_row = 2
        expenses_row = 2 + len(CATEGORIES) + 1
        rows.append(["Net Profit", f"=B{income_row}-B{expenses_row}"])

        for row in rows:
            ws_tax.append_row(row)

    # Format Amount column (D, index 3) as $ currency on Transactions and Business Expenses
    _format_currency_column(sheet, ws_tx, col_index=3)
    _format_currency_column(sheet, ws_exp, col_index=3)

    _auto_resize_all(sheet)
    print(f"  Sheet setup complete. Tabs: {TAB_TRANSACTIONS}, {TAB_EXPENSES}, {TAB_TAX_SUMMARY}")


def append_transaction(date, description, source, amount, notes=""):
    """Add one income row to the Transactions tab."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    ws.append_row([date, description, source, amount, notes])
    _auto_resize(sheet, ws)


def append_transactions(rows):
    """Add multiple income rows at once. Each row: [date, description, source, amount, notes]."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    for row in rows:
        ws.append_row(row)
    _auto_resize(sheet, ws)


def append_expense(date, vendor, category, amount, notes=""):
    """Add one row to the Business Expenses tab."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_EXPENSES)
    ws.append_row([date, vendor, category, amount, notes])
    _auto_resize(sheet, ws)


def append_expenses(rows):
    """Add multiple expense rows at once. Each row: [date, vendor, category, amount, notes]."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_EXPENSES)
    for row in rows:
        ws.append_row(row)
    _auto_resize(sheet, ws)
