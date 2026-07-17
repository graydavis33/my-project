import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

from main import dedupe_bank_alerts
from gmail_client import build_query
from config import ALERT_SENDERS
from expense_scanner import _SYSTEM_PROMPT, _validate


def test_alert_senders_in_query():
    q = build_query(30)
    for sender in ALERT_SENDERS:
        assert f"from:{sender}" in q

def test_prompt_uses_new_categories():
    category_block = _SYSTEM_PROMPT.split("category: one of")[1].split("Venmo")[0]
    for old in ["Streaming ", "Transport ", "Health & Wellness", "Shopping "]:
        assert old not in category_block
    for new in ["BJJ & Kickboxing", "Misc"]:
        assert new in _SYSTEM_PROMPT
    # Investments category removed 2026-07-17 — brokerage txns are skipped, not budgeted
    assert "Investments" not in category_block

def test_prompt_has_bank_alert_rules():
    assert "bank" in _SYSTEM_PROMPT.lower() and "alert" in _SYSTEM_PROMPT.lower()

def test_validate_maps_unknown_category_to_misc():
    r = _validate({"date": "2026-07-07", "vendor": "X", "amount": 5, "category": "Streaming"})
    assert r["category"] == "Misc"

def test_dedupe_drops_alert_matching_receipt():
    receipt = {"email_id": "a", "date": "2026-07-06", "vendor": "DoorDash", "amount": 24.50, "category": "Dining Out"}
    alert = {"email_id": "b", "date": "2026-07-07", "vendor": "DOORDASH*ORDER", "amount": 24.50, "category": "Misc", "is_alert": True}
    out = dedupe_bank_alerts([receipt, alert])
    assert out == [receipt]

def test_dedupe_keeps_unmatched_alert():
    alert = {"email_id": "b", "date": "2026-07-07", "vendor": "BODEGA NYC", "amount": 12.00, "category": "Misc", "is_alert": True}
    out = dedupe_bank_alerts([alert])
    assert out == [alert]

def test_dedupe_keeps_alert_outside_window():
    receipt = {"email_id": "a", "date": "2026-07-01", "vendor": "DoorDash", "amount": 24.50, "category": "Dining Out"}
    alert = {"email_id": "b", "date": "2026-07-07", "vendor": "DOORDASH", "amount": 24.50, "category": "Misc", "is_alert": True}
    assert len(dedupe_bank_alerts([receipt, alert])) == 2

def test_dedupe_collapses_alert_vs_alert():
    # Real case 2026-06-20: same $30 Zelle payment reported by BOTH PrimeSouth and Rocket Money
    ps = {"email_id": "a", "date": "2026-06-20", "vendor": "Barbershop", "amount": 30.00, "category": "Misc", "is_alert": True}
    rm = {"email_id": "b", "date": "2026-06-22", "vendor": "Zelle Money Payme", "amount": 30.00, "category": "Misc", "is_alert": True}
    out = dedupe_bank_alerts([ps, rm])
    assert out == [ps]  # first alert kept, duplicate dropped


# --- dedupe_vs_manual: skip email expenses Gray already typed into the app ---
from main import dedupe_vs_manual

def test_manual_dedupe_drops_late_bank_alert():
    # Real case 2026-07-08: banana tap purchase entered manually, alert posts 1-2 days later
    alert = {"email_id": "a", "date": "2026-07-09", "vendor": "GROCERY NYC", "amount": 4.50, "category": "Groceries", "is_alert": True}
    manual = [{"date": "2026-07-08", "vendor": "Bananas", "amount": 4.50, "source": "manual", "deleted": False}]
    kept, dropped = dedupe_vs_manual([alert], manual)
    assert kept == [] and dropped == [alert]

def test_manual_dedupe_keeps_unmatched_expense():
    receipt = {"email_id": "a", "date": "2026-07-09", "vendor": "Sandcastles", "amount": 49.00, "category": "Software & Tools"}
    manual = [{"date": "2026-07-08", "vendor": "Bananas", "amount": 4.50, "source": "manual", "deleted": False}]
    kept, dropped = dedupe_vs_manual([receipt], manual)
    assert kept == [receipt] and dropped == []

def test_manual_dedupe_respects_window():
    alert = {"email_id": "a", "date": "2026-07-15", "vendor": "GROCERY", "amount": 4.50, "category": "Misc", "is_alert": True}
    manual = [{"date": "2026-07-08", "vendor": "Bananas", "amount": 4.50, "source": "manual", "deleted": False}]
    kept, dropped = dedupe_vs_manual([alert], manual)
    assert kept == [alert] and dropped == []

def test_manual_dedupe_tombstone_still_suppresses():
    # Gray deleted his manual entry = he doesn't want the purchase counted
    alert = {"email_id": "a", "date": "2026-07-09", "vendor": "GROCERY", "amount": 4.50, "category": "Misc", "is_alert": True}
    manual = [{"date": "2026-07-08", "vendor": "Bananas", "amount": 4.50, "source": "manual", "deleted": True}]
    kept, dropped = dedupe_vs_manual([alert], manual)
    assert kept == []

def test_manual_dedupe_empty_manual_is_noop():
    alert = {"email_id": "a", "date": "2026-07-09", "vendor": "GROCERY", "amount": 4.50, "category": "Misc", "is_alert": True}
    kept, dropped = dedupe_vs_manual([alert], [])
    assert kept == [alert] and dropped == []
