import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

from plaid_sync import to_expense

def _txn(**kw):
    d = {
        "transaction_id": "tx123",
        "date": "2026-07-14",
        "authorized_date": "2026-07-14",
        "name": "JOE PIZZA NYC",
        "merchant_name": "Joe's Pizza",
        "amount": 18.5,
        "personal_finance_category": {"primary": "FOOD_AND_DRINK", "detailed": "FOOD_AND_DRINK_RESTAURANT"},
    }
    d.update(kw); return d

def test_purchase_maps_to_expense():
    e = to_expense(_txn())
    assert e["email_id"] == "plaid_tx123"
    assert e["vendor"] == "Joe's Pizza"
    assert e["amount"] == 18.5
    assert e["category"] == "Dining Out"
    assert e["date"] == "2026-07-14"
    assert e["source"] == "plaid"

def test_credit_or_refund_excluded():
    # Plaid depository: negative amount = money INTO the account (refund/income)
    assert to_expense(_txn(amount=-50.0)) is None

def test_zero_amount_excluded():
    assert to_expense(_txn(amount=0)) is None

def test_transfer_excluded():
    assert to_expense(_txn(
        personal_finance_category={"primary": "TRANSFER_OUT", "detailed": "TRANSFER_OUT_ACCOUNT_TRANSFER"},
    )) is None

def test_falls_back_to_name_when_no_merchant():
    e = to_expense(_txn(merchant_name=None))
    assert e["vendor"] == "JOE PIZZA NYC"

def test_date_object_is_stringified():
    import datetime
    e = to_expense(_txn(authorized_date=datetime.date(2026, 7, 14), date=datetime.date(2026, 7, 13)))
    assert e["date"] == "2026-07-14"  # authorized_date preferred

def test_plaid_client_imports():
    import plaid_client
    assert hasattr(plaid_client, "sync_transactions")
    assert hasattr(plaid_client, "create_link_token")
    assert hasattr(plaid_client, "exchange_public_token")


def test_run_plaid_sync_writes_and_dedupes(monkeypatch):
    import plaid_sync, firestore_writer
    from tests.test_firestore_writer import FakeClient2  # reuse the set/get fake

    c = FakeClient2()
    # a manual entry Gray already typed for the same purchase
    c.store["households/gray/transactions/m1"] = {
        "vendor": "Joe", "amount": 18.5, "category": "Dining Out",
        "date": "2026-07-14", "month": "2026-07", "source": "manual"}

    def fake_sync(access_token, cursor=""):
        added = [
            {"transaction_id": "dup", "date": "2026-07-14", "authorized_date": "2026-07-14",
             "name": "JOE", "merchant_name": "Joe", "amount": 18.5,
             "personal_finance_category": {"primary": "FOOD_AND_DRINK", "detailed": "FOOD_AND_DRINK_RESTAURANT"}},
            {"transaction_id": "new", "date": "2026-07-15", "authorized_date": "2026-07-15",
             "name": "BODEGA", "merchant_name": "Bodega", "amount": 6.0,
             "personal_finance_category": {"primary": "GENERAL_MERCHANDISE", "detailed": "GENERAL_MERCHANDISE_OTHER"}},
        ]
        return added, [], "NEXT_CURSOR"

    monkeypatch.setenv("PLAID_ACCESS_TOKEN", "test-token")
    written = plaid_sync.run_plaid_sync("2026-07", c, quiet=True, sync_fn=fake_sync)
    assert written == 1                                   # dup dropped, new kept
    assert "households/gray/transactions/plaid_new" in c.store
    assert "households/gray/transactions/plaid_dup" not in c.store
    assert firestore_writer.read_cursor(client=c) == "NEXT_CURSOR"


def test_quiet_mode_suppresses_money(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    import importlib, main
    importlib.reload(main)
    main.money_log("  Bodega $6.00")
    assert "Bodega" not in capsys.readouterr().out
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    importlib.reload(main)
