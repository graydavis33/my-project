"""Plaid transaction -> expense transform + the sync orchestration step.
Pure transform (to_expense) is unit-tested; run_plaid_sync (added in Task 6)
wires the network client + Firestore together."""

from category_map import map_category
from config import EXCLUDED_VENDORS


def _prev_month(month):
    y, m = int(month[:4]), int(month[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def to_expense(txn):
    """Plaid transaction dict -> expense dict, or None to exclude from the budget.
    Plaid depository amounts: positive = money OUT (a purchase)."""
    amount = txn.get("amount")
    if amount is None or amount <= 0:
        return None
    pfc = txn.get("personal_finance_category") or {}
    vendor = txn.get("merchant_name") or txn.get("name") or "Unknown"
    # Rent is Zelle/P2P to individuals — Plaid won't reliably categorize that as
    # rent, so the same vendor exclusions the gmail path applies must apply here
    if any(x.lower() in vendor.lower() for x in EXCLUDED_VENDORS):
        return None
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


def run_plaid_sync(current_month, client, quiet=False, sync_fn=None, dedupe_fn=None):
    """Pull Plaid transactions from the stored cursor, keep recent purchases,
    dedup against existing non-Plaid records, write to Firestore, tombstone
    removed pendings, advance the cursor. Returns the number written.

    Window is current + previous month: Plaid's feed lags hours-to-a-day, so a
    strict current-month filter would permanently drop month-boundary purchases
    (the cursor advances past them and they never come back)."""
    import firestore_writer

    if dedupe_fn is None:
        # main.py passes its own dedupe_vs_manual — importing main here would
        # re-execute its module body when the scanner runs as a script
        from main import dedupe_vs_manual as dedupe_fn
    if sync_fn is None:
        import plaid_client
        sync_fn = plaid_client.sync_transactions
    import os
    access_token = os.environ["PLAID_ACCESS_TOKEN"]

    cursor = firestore_writer.read_cursor(client=client)
    added, removed_ids, next_cursor = sync_fn(access_token, cursor)

    window = (current_month, _prev_month(current_month))
    expenses = [e for e in (to_expense(t) for t in added) if e]
    expenses = [e for e in expenses if e["date"][:7] in window]

    # Dedup against everything that isn't Plaid: receipt emails land hours before
    # Plaid surfaces the transaction, so gmail rows from earlier runs must
    # suppress the Plaid copy or every receipted purchase double-counts
    existing = []
    for month in window:
        existing += firestore_writer.fetch_non_plaid_transactions(month, client=client)
    expenses, dropped = dedupe_fn(expenses, existing)

    written = firestore_writer.write_expenses(expenses, client=client)
    tombstoned = firestore_writer.tombstone_removed(removed_ids, client=client)
    firestore_writer.write_cursor(next_cursor, client=client)

    if not quiet:
        for e in dropped:
            print(f"  Plaid skip (already recorded): {e['vendor']} ${e['amount']:.2f} ({e['date']})")
    print(f"  Plaid: {written} new, {tombstoned} removed/pending reconciled.")
    return written
