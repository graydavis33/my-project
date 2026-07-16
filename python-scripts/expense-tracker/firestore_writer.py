"""
firestore_writer.py
Writes scanned expenses into Firestore (households/gray/transactions/{email_id})
using create-only semantics — an existing doc is NEVER overwritten, so user edits
and tombstone deletions in the app can't be resurrected by the scanner.
One deliberate exception: tombstone_removed() sets deleted=True on plaid_* docs
when Plaid reports a pending transaction was dropped.
Inert unless the FIREBASE_SERVICE_ACCOUNT env var (service-account JSON) is set.
"""

import json
import os
import time

try:
    from google.api_core.exceptions import AlreadyExists
except ImportError:  # firebase-admin not installed (local runs without the extra)
    class AlreadyExists(Exception):
        pass

ROOT = "households/gray"
STATE = "households/gray/plaid_state/cursor"


def get_client():
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not raw:
        return None
    import firebase_admin
    from firebase_admin import credentials, firestore
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
    return firestore.client()


def _stream_month(month, client):
    return client.collection(f"{ROOT}/transactions").where("month", "==", month).stream()


def fetch_non_gmail_transactions(month, client=None):
    """This month's records NOT sourced from gmail (manual app entries + Plaid).
    Used to dedup incoming GMAIL expenses. [] when Firestore isn't configured."""
    if client is None:
        client = get_client()
    if client is None:
        return []
    return [d.to_dict() for d in _stream_month(month, client)
            if (d.to_dict() or {}).get("source") != "gmail"]


def fetch_manual_only_transactions(month, client=None):
    """This month's truly user-typed records (source not gmail/plaid). Used to
    dedup incoming PLAID expenses so a purchase Gray already typed isn't doubled."""
    if client is None:
        client = get_client()
    if client is None:
        return []
    return [d.to_dict() for d in _stream_month(month, client)
            if (d.to_dict() or {}).get("source") not in ("gmail", "plaid")]


def write_expenses(expenses, client=None):
    if client is None:
        client = get_client()
    if client is None:
        return 0
    created = 0
    now_ms = int(time.time() * 1000)
    for e in expenses:
        doc = {
            "vendor": e["vendor"],
            "amount": e["amount"],
            "category": e["category"],
            "date": e["date"],
            "month": e["date"][:7],
            "note": "",
            "source": e.get("source", "gmail"),
            "email_id": e["email_id"],
            "deleted": False,
            "createdAt": now_ms,
            "updated_at": now_ms,
        }
        if e.get("kind"):
            doc["kind"] = e["kind"]
        try:
            client.document(f"{ROOT}/transactions/{e['email_id']}").create(doc)
            created += 1
        except AlreadyExists:
            pass
    return created


def read_cursor(client=None):
    if client is None:
        client = get_client()
    if client is None:
        return ""
    snap = client.document(STATE).get()
    return (snap.to_dict() or {}).get("cursor", "") if snap.exists else ""


def write_cursor(cursor, client=None):
    if client is None:
        client = get_client()
    if client is None:
        return
    client.document(STATE).set({"cursor": cursor, "updated_at": int(time.time() * 1000)})


def tombstone_removed(removed_ids, client=None):
    """Plaid reports a pending transaction was dropped -> mark its doc deleted so
    pending+posted never double-count. Returns count actually tombstoned."""
    if client is None:
        client = get_client()
    if client is None:
        return 0
    n = 0
    for tid in removed_ids:
        ref = client.document(f"{ROOT}/transactions/plaid_{tid}")
        snap = ref.get()
        if snap.exists:
            data = snap.to_dict()
            data["deleted"] = True
            data["updated_at"] = int(time.time() * 1000)
            ref.set(data)
            n += 1
    return n
