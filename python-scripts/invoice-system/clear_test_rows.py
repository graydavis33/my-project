"""
clear_test_rows.py
One-time script to delete rows 2–9 from the Transactions tab (test data cleanup).
Run: python clear_test_rows.py
"""

from sheets_client import get_sheet
from config import TAB_TRANSACTIONS

sheet = get_sheet()
ws = sheet.worksheet(TAB_TRANSACTIONS)

# Delete from bottom up to avoid row index shifting
for row in range(9, 1, -1):
    ws.delete_rows(row)
    print(f"  Deleted row {row}")

print("\nDone. Rows 2–9 cleared from Transactions tab.")
print("The TOTAL row and Tax Summary formulas will auto-update.")
