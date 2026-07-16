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


def test_gmail_row_from_earlier_run_suppresses_plaid_copy(monkeypatch):
    # Receipt emails land hours before Plaid surfaces the txn — the gmail row
    # written by an earlier run must suppress the Plaid copy (C2 fix)
    import plaid_sync, firestore_writer
    from tests.test_firestore_writer import FakeClient2

    c = FakeClient2()
    c.store["households/gray/transactions/g1"] = {
        "vendor": "DoorDash", "amount": 24.5, "category": "Dining Out",
        "date": "2026-07-14", "month": "2026-07", "source": "gmail"}

    def fake_sync(access_token, cursor=""):
        return [{"transaction_id": "pd1", "date": "2026-07-15", "authorized_date": "2026-07-15",
                 "name": "DOORDASH*NYC", "merchant_name": "DoorDash", "amount": 24.5,
                 "personal_finance_category": {"primary": "FOOD_AND_DRINK",
                                               "detailed": "FOOD_AND_DRINK_RESTAURANT"}}], [], "CUR"

    monkeypatch.setenv("PLAID_ACCESS_TOKEN", "test-token")
    written = plaid_sync.run_plaid_sync("2026-07", c, quiet=True, sync_fn=fake_sync)
    assert written == 0
    assert "households/gray/transactions/plaid_pd1" not in c.store


def test_excluded_vendor_zelle_rent_never_an_expense():
    # Rent is Zelle/P2P — Plaid can't be trusted to categorize it as rent (I4 fix)
    from plaid_sync import to_expense
    assert to_expense({
        "transaction_id": "z1", "date": "2026-07-01", "authorized_date": "2026-07-01",
        "name": "Zelle payment to Ohana Housing", "merchant_name": "Ohana Housing",
        "amount": 1900.0,
        "personal_finance_category": {"primary": "GENERAL_SERVICES", "detailed": None},
    }) is None


def test_previous_month_kept_older_dropped(monkeypatch):
    # Plaid's feed lags — month-boundary purchases must survive (I3 fix)
    import plaid_sync
    from tests.test_firestore_writer import FakeClient2

    def fake_sync(access_token, cursor=""):
        mk = lambda tid, date: {"transaction_id": tid, "date": date, "authorized_date": date,
                                "name": "BODEGA", "merchant_name": "Bodega", "amount": 6.0,
                                "personal_finance_category": {"primary": "GENERAL_MERCHANDISE",
                                                              "detailed": None}}
        return [mk("junjul", "2026-06-30"), mk("may", "2026-05-30")], [], "CUR"

    monkeypatch.setenv("PLAID_ACCESS_TOKEN", "test-token")
    c = FakeClient2()
    written = plaid_sync.run_plaid_sync("2026-07", c, quiet=True, sync_fn=fake_sync)
    assert written == 1
    assert "households/gray/transactions/plaid_junjul" in c.store   # prev month kept
    assert "households/gray/transactions/plaid_may" not in c.store  # older dropped


def test_prev_month_january_wraps_year():
    from plaid_sync import _prev_month
    assert _prev_month("2026-01") == "2025-12"
    assert _prev_month("2026-07") == "2026-06"


def test_ci_run_output_carries_no_money(monkeypatch, capsys):
    # The spec's hard privacy requirement: with GITHUB_ACTIONS=true, a full
    # plaid-sync run over real-shaped data prints NO vendors or dollar amounts
    import re, importlib
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("PLAID_ACCESS_TOKEN", "test-token")
    import expense_scanner
    importlib.reload(expense_scanner)  # re-evaluate QUIET under CI env
    import plaid_sync
    from tests.test_firestore_writer import FakeClient2

    def fake_sync(access_token, cursor=""):
        return [{"transaction_id": "t1", "date": "2026-07-14", "authorized_date": "2026-07-14",
                 "name": "SECRETVENDOR", "merchant_name": "SecretVendor", "amount": 123.45,
                 "personal_finance_category": {"primary": "FOOD_AND_DRINK",
                                               "detailed": "FOOD_AND_DRINK_RESTAURANT"}}], [], "CUR"

    plaid_sync.run_plaid_sync("2026-07", FakeClient2(), quiet=True, sync_fn=fake_sync)
    # scanner-side: EJ transfer + extracted-expense prints must be silent in CI
    expense_scanner.money_log("    + [transfer] Edward Jones $3000.00 (tax_transfer)")
    expense_scanner.money_log("    + SecretVendor $123.45 (Dining Out)")
    out = capsys.readouterr().out
    assert "SecretVendor" not in out and "Edward Jones" not in out
    assert not re.search(r"\$\d", out), out
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    importlib.reload(expense_scanner)
