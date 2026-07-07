import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

from ej_transfers import parse_ej_transfer
from gmail_client import build_query, _extract_body
from config import TRANSFER_SENDERS
import base64


def _email(subject, body, sender="Edward Jones <online-notifications@edwardjones.com>"):
    return {"id": "x1", "from": sender, "subject": subject, "date": "Tue, 7 Jul 2026 09:08:00 -0500", "body": body}

TAX_BODY = ("Your Funds Transfer Request Has Been Scheduled This message confirms that *******IS28 scheduled "
            "the following funds transfer via Edward Jones Online Access: From: PRIMESOUTH BANK (*****2788) "
            "To: Sole Proprietor-1 (****8274) Process Date: 07/07/2026 Estimated Completion: 07/09/2026 "
            "Requested Amount: $3000 Transaction Type: Electronic Transfer from Bank")
INVEST_BODY = TAX_BODY.replace("Sole Proprietor-1 (****8274)", "Single-1 (****5514)").replace("$3000", "$100")


def test_parses_tax_transfer():
    r = parse_ej_transfer(_email("Your Funds Transfer Request Has Been Scheduled", TAX_BODY))
    assert r["kind"] == "tax_transfer"
    assert r["amount"] == 3000.0
    assert r["date"] == "2026-07-07"
    assert r["vendor"] == "Edward Jones (Sole Proprietor-1)"

def test_parses_invest_transfer():
    r = parse_ej_transfer(_email("Your Funds Transfer Request Has Been Scheduled", INVEST_BODY))
    assert r["kind"] == "invest_transfer"
    assert r["amount"] == 100.0

def test_parses_amount_with_cents_and_commas():
    body = TAX_BODY.replace("$3000", "$2,150.50")
    r = parse_ej_transfer(_email("Your Funds Transfer Request Has Been Scheduled", body))
    assert r["amount"] == 2150.50

def test_ignores_non_transfer_ej_email():
    assert parse_ej_transfer(_email("Your new statement is ready", "View your documents.")) is None

def test_ignores_non_ej_sender():
    assert parse_ej_transfer(_email("Your Funds Transfer Request Has Been Scheduled", TAX_BODY,
                                    sender="Phisher <fake@evil.com>")) is None

def test_unknown_account_returns_none():
    body = TAX_BODY.replace("Sole Proprietor-1 (****8274)", "Mystery-9 (****0000)")
    assert parse_ej_transfer(_email("Your Funds Transfer Request Has Been Scheduled", body)) is None

def test_ej_sender_in_query():
    q = build_query(30)
    for s in TRANSFER_SENDERS:
        assert f"from:{s}" in q

def test_extract_body_html_fallback():
    html = "<html><body><p>Requested Amount: <b>$3000</b></p></body></html>"
    payload = {"mimeType": "text/html",
               "body": {"data": base64.urlsafe_b64encode(html.encode()).decode()}}
    text = _extract_body(payload)
    assert "Requested Amount: $3000" in " ".join(text.split())
