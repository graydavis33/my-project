# Payday Checklist — Plaid Bank Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Feed every PrimeSouth purchase into the Payday Checklist automatically via Plaid (read-only), writing only to private Firestore, and remove all financial data from the public repo and CI logs.

**Architecture:** Extend the existing `python-scripts/expense-tracker` tool. A Plaid `/transactions/sync` pull runs inside the existing GitHub Actions scanner: pull → filter to real purchases → map to the app's 7 categories → dedup against manual entries → write to Firestore (`source:"plaid"`, create-only). Gmail receipt scanning stays as a deduped backstop; the Edward Jones email parser is untouched. `expenses.json` is retired and scrubbed from git history.

**Tech Stack:** Python 3.11, `plaid-python` SDK, `firebase-admin` (Firestore), pytest, GitHub Actions, `gh` CLI, `git-filter-repo`.

## Global Constraints

- **No financial data on any public surface** — nothing with amounts/balances/transactions in the repo, git history, or GitHub Actions logs.
- **Plaid is read-only** — Transactions product only, Production environment on the free Trial plan. Never request write/payment scopes.
- **App categories are exactly** `["Groceries", "Dining Out", "Software & Tools", "Utilities", "Investments", "BJJ & Kickboxing", "Misc"]` (from `config.PERSONAL_CATEGORIES`). Unknown → `Misc`.
- **Firestore is the only home for financial data.** Root path `households/gray`. Writes are create-only (never overwrite user edits/deletes).
- **Test convention:** every test file starts with `import os, sys` / `sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))` / `os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")` (config.py `sys.exit`s without the key). Run with `pytest` from `python-scripts/expense-tracker/`.
- **Secrets** (`PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ACCESS_TOKEN`) are GitHub Actions secrets and/or a gitignored local `.env`. Never committed, never printed.
- **Default AI model** `claude-sonnet-4-6`, Haiku `claude-haiku-4-5-20251001` — unchanged; Plaid categorization uses NO AI.

## File Structure

**New files (`python-scripts/expense-tracker/`):**
- `category_map.py` — pure: Plaid category → app category (or exclude).
- `plaid_sync.py` — pure transform (`to_expense`) + orchestration (`run_plaid_sync`).
- `plaid_client.py` — thin Plaid SDK network wrapper.
- `connect_bank.py` — one-time local Plaid Link flow; writes the access token to the GitHub secret.
- `tests/test_category_map.py`, `tests/test_plaid_sync.py` — new unit tests.

**Modified files:**
- `config.py` — Plaid env vars + software vendor overrides.
- `firestore_writer.py` — source-aware writes, two dedup fetchers, cursor read/write, removed-tombstone.
- `main.py` — call the Plaid step, quiet-mode logging, stop writing `expenses.json`.
- `requirements.txt` — add `plaid-python`.
- `tests/test_firestore_writer.py` — extend fake to cover new functions.
- `.github/workflows/expense-sync.yml` — Plaid secrets, drop the commit step.
- `web-apps/payday-checklist/index.html` — remove the `expenses.json` fetch.
- `.gitignore` — ignore `expenses.json`.

**Operational (no code):** connect PrimeSouth + dry-run; git history scrub.

---

### Task 1: Category mapping (pure)

**Files:**
- Create: `python-scripts/expense-tracker/category_map.py`
- Modify: `python-scripts/expense-tracker/config.py` (append software vendor overrides)
- Test: `python-scripts/expense-tracker/tests/test_category_map.py`

**Interfaces:**
- Consumes: `config.CATEGORY_OVERRIDES` (dict of vendor-substring → category), `config.PERSONAL_CATEGORIES`.
- Produces: `map_category(primary: str|None, detailed: str|None, vendor: str|None) -> str|None` — returns an app category, or `None` meaning "exclude from budget".

- [ ] **Step 1: Append software vendor overrides to config.py**

Add to the end of `config.py` (brand names only — no amounts, no personal data):

```python
# Plaid buckets most SaaS subscriptions as GENERAL_SERVICES/GENERAL_MERCHANDISE.
# These known brands are Software & Tools. Extend as new vendors appear (or just
# recategorize once in the app — create-only writes make the fix stick).
SOFTWARE_VENDORS = [
    "adobe", "github", "google", "anthropic", "openai", "notion",
    "sandcastles", "epidemic sound", "wispr", "figma", "vercel", "cursor",
]
for _v in SOFTWARE_VENDORS:
    CATEGORY_OVERRIDES.setdefault(_v, "Software & Tools")
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_category_map.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

from category_map import map_category

def test_groceries_uses_detailed():
    assert map_category("FOOD_AND_DRINK", "FOOD_AND_DRINK_GROCERIES", "Whole Foods") == "Groceries"

def test_restaurant_is_dining():
    assert map_category("FOOD_AND_DRINK", "FOOD_AND_DRINK_RESTAURANT", "Joe's Pizza") == "Dining Out"

def test_rent_is_excluded():
    assert map_category("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_RENT", "Ohana Housing") is None

def test_utilities_kept():
    assert map_category("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY", "Con Ed") == "Utilities"

def test_income_and_transfers_excluded():
    assert map_category("INCOME", "INCOME_WAGES", "Payroll") is None
    assert map_category("TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", "Edward Jones") is None
    assert map_category("LOAN_PAYMENTS", "LOAN_PAYMENTS_STUDENT_LOAN", "Nelnet") is None

def test_vendor_override_wins():
    # Plaid would call Adobe GENERAL_SERVICES; the override forces Software & Tools
    assert map_category("GENERAL_SERVICES", "GENERAL_SERVICES_OTHER", "Adobe Inc") == "Software & Tools"

def test_unknown_primary_falls_to_misc():
    assert map_category("SOMETHING_NEW", None, "Mystery") == "Misc"

def test_general_merchandise_is_misc():
    assert map_category("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_OTHER", "Target") == "Misc"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_category_map.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'category_map'`

- [ ] **Step 4: Write minimal implementation**

```python
# category_map.py
"""Deterministic Plaid personal_finance_category -> payday-checklist category.
Returns None for anything that isn't a discretionary budget expense (income,
transfers, rent, loan payments) so the scanner drops it."""

from config import CATEGORY_OVERRIDES

# Plaid PRIMARY category -> app category. None = exclude from the budget.
_PRIMARY = {
    "INCOME": None,
    "TRANSFER_IN": None,
    "TRANSFER_OUT": None,
    "LOAN_PAYMENTS": None,
    "BANK_FEES": "Misc",
    "ENTERTAINMENT": "Misc",
    "FOOD_AND_DRINK": "Dining Out",
    "GENERAL_MERCHANDISE": "Misc",
    "GENERAL_SERVICES": "Misc",
    "GOVERNMENT_AND_NON_PROFIT": "Misc",
    "HOME_IMPROVEMENT": "Misc",
    "MEDICAL": "Misc",
    "PERSONAL_CARE": "Misc",
    "RENT_AND_UTILITIES": "Utilities",   # rent split out in _DETAILED
    "TRANSPORTATION": "Misc",
    "TRAVEL": "Misc",
}

# DETAILED category overrides (more specific than primary).
_DETAILED = {
    "FOOD_AND_DRINK_GROCERIES": "Groceries",
    "RENT_AND_UTILITIES_RENT": None,     # rent tracked separately in the app
}


def map_category(primary, detailed, vendor):
    v = (vendor or "").lower()
    for match, cat in CATEGORY_OVERRIDES.items():
        if match.lower() in v:
            return cat
    if detailed in _DETAILED:
        return _DETAILED[detailed]
    return _PRIMARY.get(primary, "Misc")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_category_map.py -v`
Expected: PASS (8 passed)

- [ ] **Step 6: Commit**

```bash
git add python-scripts/expense-tracker/category_map.py python-scripts/expense-tracker/config.py python-scripts/expense-tracker/tests/test_category_map.py
git commit -m "feat(expense-tracker): deterministic Plaid category mapping"
```

---

### Task 2: Plaid transaction transform (pure)

**Files:**
- Create: `python-scripts/expense-tracker/plaid_sync.py` (transform only for now)
- Test: `python-scripts/expense-tracker/tests/test_plaid_sync.py`

**Interfaces:**
- Consumes: `category_map.map_category`.
- Produces: `to_expense(txn: dict) -> dict|None`. Input is a Plaid transaction dict (from `plaid_client.sync_transactions`). Output expense dict has keys `email_id` (= `"plaid_" + transaction_id`, used as the Firestore doc id), `date` (`YYYY-MM-DD`), `vendor`, `amount` (float, 2dp), `category`, `source` (`"plaid"`). Returns `None` when the transaction is not a budget expense.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plaid_sync.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plaid_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'plaid_sync'`

- [ ] **Step 3: Write minimal implementation**

```python
# plaid_sync.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plaid_sync.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add python-scripts/expense-tracker/plaid_sync.py python-scripts/expense-tracker/tests/test_plaid_sync.py
git commit -m "feat(expense-tracker): Plaid transaction -> expense transform"
```

---

### Task 3: Firestore writer — source-aware writes, dedup fetchers, cursor, tombstones

**Files:**
- Modify: `python-scripts/expense-tracker/firestore_writer.py`
- Test: `python-scripts/expense-tracker/tests/test_firestore_writer.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `write_expenses(expenses, client=None)` — now honors `e.get("source", "gmail")` (unchanged signature/behavior for gmail).
  - `fetch_non_gmail_transactions(month, client=None) -> list[dict]` — records with `source != "gmail"` (manual + plaid). **Renamed from `fetch_manual_transactions`.**
  - `fetch_manual_only_transactions(month, client=None) -> list[dict]` — records with `source` not in `("gmail","plaid")` (truly user-typed).
  - `read_cursor(client=None) -> str` — the stored Plaid sync cursor, or `""`.
  - `write_cursor(cursor, client=None)` — persist the cursor.
  - `tombstone_removed(removed_ids, client=None) -> int` — mark `plaid_<id>` docs `deleted=True`.

- [ ] **Step 1: Write the failing tests (extend the existing fake to support set/get)**

Append to `tests/test_firestore_writer.py`:

```python
# --- extended fake supporting set/get for cursor + tombstones ---
class FakeSnap:
    def __init__(self, data): self._d = data
    @property
    def exists(self): return self._d is not None
    def to_dict(self): return self._d or {}

class FakeDoc2:
    def __init__(self, store, path): self.store, self.path = store, path
    def create(self, data):
        if self.path in self.store: raise firestore_writer.AlreadyExists("exists")
        self.store[self.path] = data
    def set(self, data): self.store[self.path] = data
    def get(self): return FakeSnap(self.store.get(self.path))

class FakeQuery:
    def __init__(self, store, col): self.store, self.col = store, col
    def where(self, field, op, value):
        self._field, self._value = field, value; return self
    def stream(self):
        for path, data in self.store.items():
            if path.startswith(self.col + "/") and data.get(self._field) == self._value:
                yield FakeSnap(data)

class FakeClient2:
    def __init__(self): self.store = {}
    def document(self, path): return FakeDoc2(self.store, path)
    def collection(self, path): return FakeQuery(self.store, path)

def _rec(sid, source, amount=10.0, month="2026-07"):
    return {"vendor": "V", "amount": amount, "category": "Misc", "date": month + "-05",
            "month": month, "source": source}

def test_write_expenses_honors_source():
    c = FakeClient()
    firestore_writer.write_expenses([_exp(source="plaid", email_id="plaid_x")], client=c)
    assert c.store["households/gray/transactions/plaid_x"]["source"] == "plaid"

def test_fetch_non_gmail_includes_plaid_and_manual():
    c = FakeClient2()
    c.store["households/gray/transactions/g1"] = _rec("g1", "gmail")
    c.store["households/gray/transactions/plaid_p1"] = _rec("plaid_p1", "plaid")
    c.store["households/gray/transactions/m1"] = _rec("m1", "manual")
    out = firestore_writer.fetch_non_gmail_transactions("2026-07", client=c)
    sources = sorted(r["source"] for r in out)
    assert sources == ["manual", "plaid"]

def test_fetch_manual_only_excludes_plaid():
    c = FakeClient2()
    c.store["households/gray/transactions/plaid_p1"] = _rec("plaid_p1", "plaid")
    c.store["households/gray/transactions/m1"] = _rec("m1", "manual")
    out = firestore_writer.fetch_manual_only_transactions("2026-07", client=c)
    assert [r["source"] for r in out] == ["manual"]

def test_cursor_roundtrip():
    c = FakeClient2()
    assert firestore_writer.read_cursor(client=c) == ""
    firestore_writer.write_cursor("CURSOR_ABC", client=c)
    assert firestore_writer.read_cursor(client=c) == "CURSOR_ABC"

def test_tombstone_removed_marks_deleted():
    c = FakeClient2()
    c.store["households/gray/transactions/plaid_p1"] = _rec("plaid_p1", "plaid")
    n = firestore_writer.tombstone_removed(["p1"], client=c)
    assert n == 1
    assert c.store["households/gray/transactions/plaid_p1"]["deleted"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_firestore_writer.py -v`
Expected: FAIL (`AttributeError: module 'firestore_writer' has no attribute 'fetch_non_gmail_transactions'`, etc.)

- [ ] **Step 3: Implement the changes**

In `firestore_writer.py`, change the hardcoded source in `write_expenses` from `"source": "gmail",` to:

```python
            "source": e.get("source", "gmail"),
```

Replace the existing `fetch_manual_transactions` function with the two fetchers below, and add the cursor + tombstone helpers:

```python
STATE = "households/gray/plaid_state/cursor"


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
```

- [ ] **Step 4: Update the caller in main.py (rename only)**

In `main.py`, change the gmail dedup fetch call from `firestore_writer.fetch_manual_transactions(current_month, client=fs_client)` to:

```python
        manual = firestore_writer.fetch_non_gmail_transactions(current_month, client=fs_client)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_firestore_writer.py -v`
Expected: PASS (all, including the pre-existing tests)

- [ ] **Step 6: Commit**

```bash
git add python-scripts/expense-tracker/firestore_writer.py python-scripts/expense-tracker/main.py python-scripts/expense-tracker/tests/test_firestore_writer.py
git commit -m "feat(expense-tracker): source-aware writes, plaid dedup fetchers, cursor + tombstones"
```

---

### Task 4: Plaid network client + dependency

**Files:**
- Create: `python-scripts/expense-tracker/plaid_client.py`
- Modify: `python-scripts/expense-tracker/config.py` (Plaid env vars)
- Modify: `python-scripts/expense-tracker/requirements.txt`
- Test: `python-scripts/expense-tracker/tests/test_plaid_sync.py` (import-guard test only)

**Interfaces:**
- Consumes: env `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV` (default `production`).
- Produces:
  - `create_link_token() -> str`
  - `exchange_public_token(public_token) -> str` (access token)
  - `sync_transactions(access_token, cursor="") -> (added: list[dict], removed_ids: list[str], next_cursor: str)`

> Network wrapper — verified against Plaid **Sandbox** (Task 9), not unit-tested. Keep it dumb so all logic lives in the pure modules.

- [ ] **Step 1: Add the dependency**

Append to `requirements.txt`:

```
plaid-python
```

Install locally:

Run: `pip install plaid-python`
Expected: installs without error.

- [ ] **Step 2: Add Plaid config**

Append to `config.py`:

```python
# Plaid (read-only Transactions). Secrets live in .env locally / Actions secrets in CI.
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "production")
PLAID_ACCESS_TOKEN = os.getenv("PLAID_ACCESS_TOKEN")
```

- [ ] **Step 3: Write plaid_client.py**

```python
# plaid_client.py
"""Thin read-only wrapper over the Plaid Transactions API. All decision logic
lives in plaid_sync/category_map; this only talks to Plaid."""

import os
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

_ENVS = {"sandbox": plaid.Environment.Sandbox, "production": plaid.Environment.Production}


def _api():
    cfg = plaid.Configuration(
        host=_ENVS[os.getenv("PLAID_ENV", "production")],
        api_key={"clientId": os.environ["PLAID_CLIENT_ID"], "secret": os.environ["PLAID_SECRET"]},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(cfg))


def create_link_token():
    req = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="gray"),
        client_name="Payday Checklist",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
    )
    return _api().link_token_create(req).link_token


def exchange_public_token(public_token):
    req = ItemPublicTokenExchangeRequest(public_token=public_token)
    return _api().item_public_token_exchange(req).access_token


def sync_transactions(access_token, cursor=""):
    """Page /transactions/sync to exhaustion. Returns (added, removed_ids, next_cursor).
    'modified' are folded into 'added' (create-only write skips ones already stored)."""
    added, removed = [], []
    api = _api()
    while True:
        kwargs = {"access_token": access_token}
        if cursor:
            kwargs["cursor"] = cursor
        resp = api.transactions_sync(TransactionsSyncRequest(**kwargs))
        added += [t.to_dict() for t in resp.added]
        added += [t.to_dict() for t in resp.modified]
        removed += [t.transaction_id for t in resp.removed]
        cursor = resp.next_cursor
        if not resp.has_more:
            break
    return added, removed, cursor
```

- [ ] **Step 4: Add an import-guard test**

Append to `tests/test_plaid_sync.py`:

```python
def test_plaid_client_imports():
    import plaid_client
    assert hasattr(plaid_client, "sync_transactions")
    assert hasattr(plaid_client, "create_link_token")
    assert hasattr(plaid_client, "exchange_public_token")
```

- [ ] **Step 5: Run the test**

Run: `pytest tests/test_plaid_sync.py -v`
Expected: PASS (import succeeds now that `plaid-python` is installed)

- [ ] **Step 6: Commit**

```bash
git add python-scripts/expense-tracker/plaid_client.py python-scripts/expense-tracker/config.py python-scripts/expense-tracker/requirements.txt python-scripts/expense-tracker/tests/test_plaid_sync.py
git commit -m "feat(expense-tracker): Plaid read-only network client + dependency"
```

---

### Task 5: One-time bank-connect script

**Files:**
- Create: `python-scripts/expense-tracker/connect_bank.py`

**Interfaces:**
- Consumes: `plaid_client.create_link_token`, `plaid_client.exchange_public_token`; `gh` CLI on PATH.
- Produces: sets the `PLAID_ACCESS_TOKEN` GitHub Actions secret. Interactive; not unit-tested.

- [ ] **Step 1: Write connect_bank.py**

```python
# connect_bank.py
"""One-time, local: open Plaid Link, connect PrimeSouth, capture the read-only
access token, and push it to the PLAID_ACCESS_TOKEN GitHub secret. The token is
never written to a repo file and never printed.

Prereqs: PLAID_CLIENT_ID + PLAID_SECRET in .env, PLAID_ENV=production, and the
`gh` CLI authenticated (`gh auth status`). Run:  python connect_bank.py
"""

import http.server
import json
import subprocess
import urllib.parse
import webbrowser

import plaid_client

REPO = "graydavis33/my-project"
PORT = 8712

PAGE = """<!doctype html><html><body>
<script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
<script>
const handler = Plaid.create({
  token: "%s",
  onSuccess: (public_token) => {
    fetch("/exchange", {method:"POST", body: JSON.stringify({public_token})})
      .then(() => document.body.innerHTML = "<h2>Connected. You can close this tab.</h2>");
  },
  onExit: () => document.body.innerHTML = "<h2>Cancelled.</h2>",
});
handler.open();
</script>
Opening Plaid...
</body></html>"""


def main():
    link_token = plaid_client.create_link_token()
    done = {"ok": False}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write((PAGE % link_token).encode())
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            public_token = json.loads(body)["public_token"]
            access_token = plaid_client.exchange_public_token(public_token)
            subprocess.run(["gh", "secret", "set", "PLAID_ACCESS_TOKEN", "--repo", REPO],
                           input=access_token, text=True, check=True)
            self.send_response(200); self.end_headers()
            done["ok"] = True
            print("PLAID_ACCESS_TOKEN secret set. PrimeSouth connected.")

    srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
    webbrowser.open(f"http://127.0.0.1:{PORT}/")
    print(f"Complete the bank login in your browser ({srv.server_address[0]}:{PORT})...")
    while not done["ok"]:
        srv.handle_request()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it imports (no run yet — the live run is Task 9)**

Run: `python -c "import connect_bank"`
Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add python-scripts/expense-tracker/connect_bank.py
git commit -m "feat(expense-tracker): one-time Plaid Link connect script"
```

---

### Task 6: Wire Plaid into main.py + quiet-mode logging + stop writing expenses.json

**Files:**
- Modify: `python-scripts/expense-tracker/plaid_sync.py` (add `run_plaid_sync`)
- Modify: `python-scripts/expense-tracker/main.py`
- Test: `python-scripts/expense-tracker/tests/test_plaid_sync.py`

**Interfaces:**
- Consumes: `plaid_client.sync_transactions`, `firestore_writer` (cursor, dedup, write, tombstone), `main.dedupe_vs_manual`.
- Produces: `run_plaid_sync(current_month, client, quiet=False, sync_fn=None) -> int` (count written). `sync_fn` defaults to `plaid_client.sync_transactions`; injectable for tests.

- [ ] **Step 1: Write the failing test**

```python
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

    written = plaid_sync.run_plaid_sync("2026-07", c, quiet=True, sync_fn=fake_sync)
    assert written == 1                                   # dup dropped, new kept
    assert "households/gray/transactions/plaid_new" in c.store
    assert "households/gray/transactions/plaid_dup" not in c.store
    assert firestore_writer.read_cursor(client=c) == "NEXT_CURSOR"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plaid_sync.py::test_run_plaid_sync_writes_and_dedupes -v`
Expected: FAIL (`AttributeError: module 'plaid_sync' has no attribute 'run_plaid_sync'`)

- [ ] **Step 3: Implement run_plaid_sync in plaid_sync.py**

Append to `plaid_sync.py`:

```python
def run_plaid_sync(current_month, client, quiet=False, sync_fn=None):
    """Pull Plaid transactions from the stored cursor, keep this-month purchases,
    dedup against manual entries, write to Firestore, tombstone removed pendings,
    advance the cursor. Returns the number of new records written."""
    import firestore_writer
    from main import dedupe_vs_manual

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
    expenses, dropped = dedupe_vs_manual(expenses, manual)

    written = firestore_writer.write_expenses(expenses, client=client)
    tombstoned = firestore_writer.tombstone_removed(removed_ids, client=client)
    firestore_writer.write_cursor(next_cursor, client=client)

    if not quiet:
        for e in dropped:
            print(f"  Plaid skip (manual dup): {e['vendor']} ${e['amount']:.2f} ({e['date']})")
    print(f"  Plaid: {written} new, {tombstoned} removed/pending reconciled.")
    return written
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plaid_sync.py -v`
Expected: PASS

- [ ] **Step 5: Add the quiet-mode guard + Plaid step to main.py**

In `main.py`, add near the top (after imports):

```python
QUIET = os.getenv("GITHUB_ACTIONS") == "true"  # Actions logs are public — no $ in CI


def money_log(msg):
    if not QUIET:
        print(msg)
```

Change the four financial `print(...)` lines that include a vendor, amount, or category total to `money_log(...)`:
- line ~147 `print(f"    - {e['vendor']} ${e['amount']:.2f} ({e['date']})")` → `money_log(...)`
- line ~167 `print(f"  Skipped (already entered manually in app): ...")` → `money_log(...)`
- line ~177 `print(f"  {cat}: ${total:.2f}")` → `money_log(...)`
- the per-category summary loop header stays, but wrap the amount line as above.

In `main()`, after `fs_client = firestore_writer.get_client()` is obtained (it's currently fetched later — move the `get_client()` call up to just after Gmail connect, or fetch it before the Plaid step), insert the Plaid step **before** the Gmail dedup block so Gmail dedups against fresh Plaid writes:

```python
    # --- Plaid: primary purchase feed (writes to Firestore, never expenses.json) ---
    if fs_client and os.getenv("PLAID_ACCESS_TOKEN"):
        import plaid_sync
        plaid_sync.run_plaid_sync(current_month, fs_client, quiet=QUIET)
    else:
        print("Plaid: skipped (PLAID_ACCESS_TOKEN or Firestore not set).")
```

Remove the `expenses.json` write: delete the `write_expenses_json(expenses, current_month, transfers)` call (and the now-unused `write_expenses_json` function + `EXPENSES_OUTPUT_PATH` import if nothing else uses them). Keep the Firestore `write_expenses(expenses + transfers, ...)` call.

- [ ] **Step 6: Add a quiet-mode test**

Append to `tests/test_plaid_sync.py`:

```python
def test_quiet_mode_suppresses_money(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    import importlib, main
    importlib.reload(main)
    main.money_log("  Bodega $6.00")
    assert "Bodega" not in capsys.readouterr().out
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    importlib.reload(main)
```

- [ ] **Step 7: Run the full suite**

Run: `pytest -v`
Expected: PASS (all tests across every file green)

- [ ] **Step 8: Commit**

```bash
git add python-scripts/expense-tracker/plaid_sync.py python-scripts/expense-tracker/main.py python-scripts/expense-tracker/tests/test_plaid_sync.py
git commit -m "feat(expense-tracker): wire Plaid step, quiet CI logs, drop expenses.json write"
```

---

### Task 7: Workflow — add Plaid secrets, drop the commit step

**Files:**
- Modify: `.github/workflows/expense-sync.yml`

**Interfaces:** none (CI config).

- [ ] **Step 1: Add Plaid env to the run step**

In the "Run expense scanner" step, add the three Plaid secrets and env to the existing `env:` block:

```yaml
      - name: Run expense scanner
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          FIREBASE_SERVICE_ACCOUNT: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          PLAID_CLIENT_ID: ${{ secrets.PLAID_CLIENT_ID }}
          PLAID_SECRET: ${{ secrets.PLAID_SECRET }}
          PLAID_ACCESS_TOKEN: ${{ secrets.PLAID_ACCESS_TOKEN }}
          PLAID_ENV: production
        run: cd python-scripts/expense-tracker && python main.py
```

- [ ] **Step 2: Remove the expenses.json commit step and downgrade permissions**

Delete the entire final step:

```yaml
      - name: Commit updated expenses.json
        run: |
          ...
          git push
```

Change `permissions: contents: write` to `permissions: contents: read` (nothing is committed now; all data goes to Firestore).

- [ ] **Step 3: Verify the YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/expense-sync.yml'))"`
Expected: no error.

- [ ] **Step 4: Confirm no commit/push remains**

Run: `grep -nE 'git (add|commit|push)|expenses.json' .github/workflows/expense-sync.yml`
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/expense-sync.yml
git commit -m "ci(expense-sync): Plaid secrets, drop public expenses.json commit"
```

> **Manual (Gray, before this workflow runs live):** add repo secrets `PLAID_CLIENT_ID`, `PLAID_SECRET` (and `PLAID_ACCESS_TOKEN`, set automatically by `connect_bank.py` in Task 9). `gh secret set PLAID_CLIENT_ID --repo graydavis33/my-project` etc.

---

### Task 8: App — stop fetching expenses.json (Firestore is the source of truth)

**Files:**
- Modify: `web-apps/payday-checklist/index.html`

**Interfaces:** none.

- [ ] **Step 1: Locate the fetch**

Run: `grep -n "expenses.json\|loadGmailExpenses\|GMAIL AUTO-SYNC" web-apps/payday-checklist/index.html`
Expected: the `GMAIL AUTO-SYNC` block (~line 1157) that does `fetch('./expenses.json' ...)` and the `Sync.init()` call site.

- [ ] **Step 2: Remove the fetch block and its call**

Delete the `loadGmailExpenses` function (the block from the `// GMAIL AUTO-SYNC ...` comment through the end of that function, ~lines 1157–1220) and any call to it in the init sequence. Leave `Sync.init()` and everything else intact — signed-in devices already receive gmail/plaid/EJ records live from Firestore.

- [ ] **Step 3: Verify the EJ card still reads from Firestore**

Run: `grep -n "kind\|Edward Jones\|ej-\|tax_transfer\|invest_transfer" web-apps/payday-checklist/index.html | head`
Expected: the EJ card logic keys off the transaction `kind` field (which arrives via the Firestore subscription in `sync.js` `applyRemote`). Confirm no EJ display path depends on `expenses.json`. If any does, repoint it to read from the transaction store.

- [ ] **Step 4: Manual smoke (local)**

Open `web-apps/payday-checklist/index.html` in a browser (signed out is fine): confirm no console error about a missing `expenses.json` and the app renders.

- [ ] **Step 5: Commit**

```bash
git add web-apps/payday-checklist/index.html
git commit -m "feat(payday): read expenses from Firestore only, drop expenses.json fetch"
```

---

### Task 9: Connect PrimeSouth + first live dry-run (operational, gated)

**Files:** none (runbook). Do this with Gray present.

- [ ] **Step 1: Local .env**

In `python-scripts/expense-tracker/.env` (gitignored) add `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV=production`, and `FIREBASE_SERVICE_ACCOUNT` (for the dry-run to read the cursor/manual entries). Gray fills these — never printed or committed.

- [ ] **Step 2: Connect the bank**

Run: `cd python-scripts/expense-tracker && python connect_bank.py`
Complete the PrimeSouth login in the browser. Expected: "PLAID_ACCESS_TOKEN secret set. PrimeSouth connected."
**This is the coverage test.** If PrimeSouth is not searchable/connectable in Plaid Link, stop and fall back to SimpleFIN or CSV (see spec risks).

- [ ] **Step 3: Dry-run the Plaid pull (no writes)**

Add a `--dry-run` guard to `run_plaid_sync` invocation for this step, or run a one-off:

Run: `python -c "import os; os.environ['PLAID_ACCESS_TOKEN']=open('.env').read().split('PLAID_ACCESS_TOKEN=')[1].splitlines()[0] if 'PLAID_ACCESS_TOKEN' in open('.env').read() else __import__('sys').exit('set token'); import plaid_client, plaid_sync; a,r,c=plaid_client.sync_transactions(os.environ['PLAID_ACCESS_TOKEN']); print(len(a),'txns'); [print(plaid_sync.to_expense(t)) for t in a[:15]]"`
Expected: prints recent transactions mapped to expenses — eyeball categories + amounts. (Run locally only; this prints money, so never in CI.)

- [ ] **Step 4: First real run**

Run: `cd python-scripts/expense-tracker && python main.py`
Expected: "Plaid: N new, ..." and Firestore populated. Open the app signed in → the Plaid transactions appear.

- [ ] **Step 5: No commit** (operational). Note results for Gray.

---

### Task 10: Retire expenses.json + gitignore

**Files:**
- Delete (tracked): `web-apps/payday-checklist/expenses.json`
- Modify: `.gitignore`

- [ ] **Step 1: Add to .gitignore**

Append to `.gitignore`:

```
# Financial data lives in Firestore only — never commit it
web-apps/payday-checklist/expenses.json
```

- [ ] **Step 2: Untrack the file**

Run: `git rm --cached web-apps/payday-checklist/expenses.json`
Expected: `rm 'web-apps/payday-checklist/expenses.json'`

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(payday): stop tracking expenses.json (Firestore-only)"
```

> Note: this removes it from the working tree/HEAD going forward. The 193 historical versions are still in git history until Task 11.

---

### Task 11: Scrub expenses.json from git history (gated — Gray's explicit go)

**Files:** whole-repo history rewrite. **Irreversible; do it deliberately, with Gray, when no session is mid-write.**

- [ ] **Step 1: Pre-flight**

- Confirm the auto-commit Stop/PreCompact hooks won't fire mid-rewrite (finish/close other Claude sessions).
- Back up: `git clone --mirror . ../my-project-backup.git`
- Install: `pip install git-filter-repo` (or `pipx install git-filter-repo`).

- [ ] **Step 2: Rewrite history**

Run:
```bash
git filter-repo --path web-apps/payday-checklist/expenses.json --invert-paths --force
```
Expected: filter-repo removes the path from all commits.

- [ ] **Step 3: Re-add origin (filter-repo drops it) and force-push**

Run:
```bash
git remote add origin https://github.com/graydavis33/my-project.git
git push origin --force --all
git push origin --force --tags
```
Expected: force-push succeeds; GitHub no longer serves the file at any commit.

- [ ] **Step 4: Verify the scrub**

Run: `git log --oneline -- web-apps/payday-checklist/expenses.json`
Expected: empty output (no history references the file).

- [ ] **Step 5: Re-clone on the Mac**

On the Mac: delete the old clone and `git clone` fresh (all SHAs changed; a plain `git pull` will conflict).

- [ ] **Step 6: Note in decisions/log.md**

Append a dated entry recording the history rewrite (date, reason, that the Mac re-cloned), then commit it normally.

---

## Self-Review

**Spec coverage:**
- Plaid primary feed → Tasks 2,4,6. ✅
- Read-only Transactions → Task 4 (Products("transactions") only). ✅
- Gmail backstop, deduped vs plaid → Task 3 (`fetch_non_gmail_transactions`) + existing `dedupe_vs_manual`. ✅
- EJ email parser kept → untouched (main.py EJ path not modified). ✅
- Firestore-only, no expenses.json → Tasks 6 (stop write), 8 (stop fetch), 10 (untrack). ✅
- Deterministic categorization → Task 1. ✅
- Pending/posted no double-count → Task 3 (`tombstone_removed`) + Task 6 (removed_ids). ✅
- CI logs silent on money → Task 6 (`QUIET`/`money_log`) + Task 7 (drop commit). ✅
- Plaid secrets never public → Tasks 5,7,9 (secrets/.env, `gh secret set`). ✅
- Git history scrub → Task 11. ✅
- One-time connect + coverage test → Tasks 5,9. ✅
- Cursor storage in Firestore → Task 3 (`read_cursor`/`write_cursor`). ✅

**Placeholder scan:** no TBD/TODO; every code step shows complete code. ✅

**Type consistency:** `to_expense` output keys (`email_id`,`date`,`vendor`,`amount`,`category`,`source`) match `write_expenses` expectations; `sync_transactions` returns `(added, removed_ids, next_cursor)` consumed identically in `run_plaid_sync`; `fetch_non_gmail_transactions` used for gmail dedup (Task 3 Step 4) and `fetch_manual_only_transactions` for plaid dedup (Task 6). ✅

**Known limitation (documented in spec):** Plaid `modified` transactions are folded into `added` and skipped by create-only writes, so a pending→posted amount change on the *same* transaction id won't update; the common pending→posted case uses distinct ids (removed + added) and is handled. Acceptable for MVP; Gray can recategorize/edit in-app.
