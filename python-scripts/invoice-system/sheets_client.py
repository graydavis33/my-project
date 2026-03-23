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


def _find_totals_row(ws):
    """Return the 1-based row index of the TOTAL row, or None if not found."""
    col_a = ws.col_values(1)
    for i, val in enumerate(col_a):
        if val == "TOTAL":
            return i + 1
    return None


def _format_totals_row(spreadsheet, ws, row_idx):
    """Apply bold + gray background to the TOTAL row."""
    spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": row_idx - 1,
                "endRowIndex": row_idx,
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


def _place_totals_row_at_bottom(spreadsheet, ws):
    """
    Remove any existing TOTAL row and place a fresh one just below the last data row.
    New rows are inserted before the TOTAL row, so Google Sheets auto-expands the SUM.
    """
    existing = _find_totals_row(ws)
    if existing:
        ws.delete_rows(existing)

    all_vals = ws.get_all_values()
    last_data_row = 1
    for i, row in enumerate(all_vals):
        if any(cell.strip() for cell in row):
            last_data_row = i + 1

    target_row = last_data_row + 1
    ws.insert_row(["TOTAL", "", "", '=SUMIF(A2:A1000,"<>TOTAL",D2:D1000)', ""], index=target_row, value_input_option="USER_ENTERED")
    _format_totals_row(spreadsheet, ws, target_row)


def _insert_before_totals(ws, row_data):
    """Insert a data row just above the TOTAL row, bumping it down. Falls back to append."""
    total_row = _find_totals_row(ws)
    if total_row:
        ws.insert_row(row_data, index=total_row)
    else:
        ws.append_row(row_data)


def _freeze_rows(spreadsheet, ws, count=1):
    """Freeze the top N rows (default: header only)."""
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

    # Place TOTAL row at bottom of data and freeze header row only
    for ws in [ws_tx, ws_exp]:
        _place_totals_row_at_bottom(sheet, ws)
        _freeze_rows(sheet, ws, count=1)

    # Always rebuild Tax Summary — uses SUMIF to exclude the TOTAL row automatically
    ws_tax.clear()
    ws_tax.append_row(TAX_SUMMARY_HEADERS)
    if True:
        tx = TAB_TRANSACTIONS
        exp = TAB_EXPENSES

        rows = []

        # Total Income — SUMIF excludes the TOTAL row regardless of where it moves
        rows.append(["Total Income", f"=SUMIF('{tx}'!A:A,\"<>TOTAL\",'{tx}'!D:D)"])

        # Expense categories — SUMPRODUCT filtered to exclude TOTAL row
        for cat in CATEGORIES:
            formula = (
                f"=SUMPRODUCT(('{exp}'!A2:A1000<>\"TOTAL\")*"
                f"('{exp}'!C2:C1000=\"{cat}\")*"
                f"('{exp}'!D2:D1000))"
            )
            rows.append([cat, formula])

        # Total Expenses — SUMIF excludes the TOTAL row
        rows.append(["Total Expenses", f"=SUMIF('{exp}'!A:A,\"<>TOTAL\",'{exp}'!D:D)"])

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
    """Add one income row to the Transactions tab (inserted above TOTAL row)."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    _insert_before_totals(ws, [date, description, source, amount, notes])
    _auto_resize(sheet, ws)


def append_transactions(rows):
    """Add multiple income rows at once. Each row: [date, description, source, amount, notes]."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    for row in rows:
        _insert_before_totals(ws, row)
    _auto_resize(sheet, ws)


def append_expense(date, vendor, category, amount, notes=""):
    """Add one row to the Business Expenses tab (inserted above TOTAL row)."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_EXPENSES)
    _insert_before_totals(ws, [date, vendor, category, amount, notes])
    _auto_resize(sheet, ws)


def append_expenses(rows):
    """Add multiple expense rows at once. Each row: [date, vendor, category, amount, notes]."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_EXPENSES)
    for row in rows:
        _insert_before_totals(ws, row)
    _auto_resize(sheet, ws)
