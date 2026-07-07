"""
firestore_writer.py
Writes scanned expenses into Firestore (households/gray/transactions/{email_id})
using create-only semantics — an existing doc is NEVER overwritten, so user edits
and tombstone deletions in the app can't be resurrected by the scanner.
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


def get_client():
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not raw:
        return None
    import firebase_admin
    from firebase_admin import credentials, firestore
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
    return firestore.client()


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
            "source": "gmail",
            "email_id": e["email_id"],
            "deleted": False,
            "createdAt": now_ms,
            "updated_at": now_ms,
        }
        try:
            client.document(f"{ROOT}/transactions/{e['email_id']}").create(doc)
            created += 1
        except AlreadyExists:
            pass
    return created
