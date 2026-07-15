"""Plaid transaction -> expense transform + the sync orchestration step.
Pure transform (to_expense) is unit-tested; run_plaid_sync (added in Task 6)
wires the network client + Firestore together."""

from category_map import map_category


def to_expense(txn):
    """Plaid transaction dict -> expense dict, or None to exclude from the budget.
    Plaid depository amounts: positive = money OUT (a purchase)."""
    amount = txn.get("amount")
    if amount is None or amount <= 0:
        return None
    pfc = txn.get("personal_finance_category") or {}
    vendor = txn.get("merchant_name") or txn.get("name") or "Unknown"
    category = map_category(pfc.get("primary"), pfc.get("detailed"), vendor)
    if category is None:
        return None
    raw_date = txn.get("authorized_date") or txn.get("date")
    return {
        "email_id": "plaid_" + txn["transaction_id"],
        "date": str(raw_date)[:10],
        "vendor": vendor,
        "amount": round(float(amount), 2),
        "category": category,
        "source": "plaid",
    }
