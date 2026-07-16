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


def run_plaid_sync(current_month, client, quiet=False, sync_fn=None, dedupe_fn=None):
    """Pull Plaid transactions from the stored cursor, keep this-month purchases,
    dedup against manual entries, write to Firestore, tombstone removed pendings,
    advance the cursor. Returns the number of new records written."""
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

    expenses = [e for e in (to_expense(t) for t in added) if e]
    expenses = [e for e in expenses if e["date"].startswith(current_month)]

    manual = firestore_writer.fetch_manual_only_transactions(current_month, client=client)
    expenses, dropped = dedupe_fn(expenses, manual)

    written = firestore_writer.write_expenses(expenses, client=client)
    tombstoned = firestore_writer.tombstone_removed(removed_ids, client=client)
    firestore_writer.write_cursor(next_cursor, client=client)

    if not quiet:
        for e in dropped:
            print(f"  Plaid skip (manual dup): {e['vendor']} ${e['amount']:.2f} ({e['date']})")
    print(f"  Plaid: {written} new, {tombstoned} removed/pending reconciled.")
    return written
