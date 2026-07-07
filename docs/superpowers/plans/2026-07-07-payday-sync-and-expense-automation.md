# Payday Checklist Phase 2 — Firebase Sync + Full Expense Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cross-device sync (iPhone PWA ↔ Windows) via Firestore, plus full expense capture: PrimeSouth bank-alert emails through the existing Gmail scanner at a 30-minute cadence.

**Architecture:** Firestore (`households/gray/...`) becomes the single source of truth. The app keeps IndexedDB as its local store; a new `sync.js` mirrors local mutations to a pluggable backend and applies remote snapshots with last-write-wins + tombstones. The Python scanner gains a `firestore_writer` (admin SDK, create-only semantics) and bank-alert parsing; everything degrades gracefully when Firebase isn't configured yet.

**Tech Stack:** Vanilla JS PWA (GitHub Pages), Firebase compat SDK (self-hosted), IndexedDB, Python + firebase-admin + Haiku, Playwright e2e (fake backend — no Java on this machine, so no emulator).

**Spec:** `docs/superpowers/specs/2026-07-07-payday-sync-and-expense-automation-design.md`

## Global Constraints

- Fixed Firestore root path: `households/gray` (no uid coupling; rules gate on email `graydavis33@gmail.com`)
- App must behave EXACTLY as Phase 1 when `window.FIREBASE_CONFIG` is null (config-flag inert deploy)
- Scanner must behave EXACTLY as today when `FIREBASE_SERVICE_ACCOUNT` env is absent (keeps writing expenses.json; it also keeps writing expenses.json when the env IS present, until post-smoke cutover)
- Firebase JS SDK self-hosted in `web-apps/payday-checklist/lib/` (SW must cache it; no CDN at runtime)
- All 46 existing e2e tests stay green after every task
- Doc + code in the same commit (house rule)
- No paid API calls in automated tests (Haiku extraction is not unit-tested live)
- Python code: no new type annotations/docstring styles beyond what files already use

## File Structure

- `web-apps/payday-checklist/tests/test_payday.py` — rescued Phase 1 e2e suite (from old session scratchpad)
- `web-apps/payday-checklist/tests/test_sync.py` — new sync e2e (2 contexts + fake backend)
- `web-apps/payday-checklist/tests/serve.py` — shared test server (static + `/fake/*` in-memory backend)
- `web-apps/payday-checklist/lib/firebase-{app,auth,firestore}-compat.js` — vendored SDK
- `web-apps/payday-checklist/firebase-config.js` — `window.FIREBASE_CONFIG = null;` until Gray's project exists
- `web-apps/payday-checklist/sync.js` — backend interface + FirebaseBackend + sync engine
- `web-apps/payday-checklist/index.html` — IDB hooks (sid/tombstones/updatedAt), sync UI row, script tags
- `web-apps/payday-checklist/sw.js` — cache v3 + new precache entries
- `web-apps/payday-checklist/firestore.rules` — rules Gray pastes into the console
- `python-scripts/expense-tracker/{config,gmail_client,expense_scanner,main}.py` — 7-category prompt, ALERT_SENDERS, alert dedup, `--dry-run`, Firestore wiring
- `python-scripts/expense-tracker/firestore_writer.py` — admin-SDK writer (create-only)
- `python-scripts/expense-tracker/tests/test_scanner.py` — pytest unit tests
- `.github/workflows/expense-sync.yml` — `*/30` cron, concurrency, optional secret
- `web-apps/payday-checklist/PHASE2-HANDOFF.md` — Gray's only-human-steps checklist

---

### Task 1: Rescue the Phase 1 e2e suite into the repo

**Files:**
- Create: `web-apps/payday-checklist/tests/test_payday.py` (copy from `C:\Users\GRAYDA~1\AppData\Local\Temp\claude\c--Users-Gray-Davis-my-project\54f4ef8a-f697-4b70-b914-c0d026b07a03\scratchpad\test_payday.py`)
- Create: `web-apps/payday-checklist/tests/serve.py`

**Interfaces:**
- Produces: `serve.py` exposing `start_server(port) -> httpd` serving the `web-apps/` directory, importable by both test files.

- [ ] **Step 1:** Copy the scratchpad suite into `tests/test_payday.py`. Replace the hardcoded `WEBAPPS_DIR = r"c:/Users/Gray Davis/my-project/web-apps"` with `WEBAPPS_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))` and move the server block into `serve.py`:

```python
"""serve.py — shared static server for payday e2e tests, plus /fake/* in-memory sync backend."""
import http.server, json, os, socketserver, threading

WEBAPPS_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

FAKE = {"docs": {}, "rev": 0}   # {"docs": {"transactions/abc": {...}}, "rev": n}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEBAPPS_DIR, **kw)
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/fake/state"):
            body = json.dumps(FAKE).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()
    def do_POST(self):
        if self.path == "/fake/set":
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n))
            FAKE["docs"][payload["path"]] = payload["data"]
            FAKE["rev"] += 1
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers()
            self.wfile.write(b"{}")
            return
        if self.path == "/fake/reset":
            FAKE["docs"] = {}; FAKE["rev"] = 0
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers()
            self.wfile.write(b"{}")
            return
        self.send_response(404); self.end_headers()

def start_server(port):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
```

In `test_payday.py`, replace the inline server block with `from serve import start_server, WEBAPPS_DIR` + `httpd = start_server(PORT)` (add `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` first). Everything else stays byte-identical.

- [ ] **Step 2:** Run: `python web-apps/payday-checklist/tests/test_payday.py` — Expected: `46 passed, 0 failed` (same as the July 6 run).
- [ ] **Step 3:** Commit: `git add web-apps/payday-checklist/tests && git commit -m "payday: rescue Phase 1 e2e suite into repo (46 tests)"`

---

### Task 2: Scanner — 7-category prompt, bank-alert parsing, alert dedup, --dry-run

**Files:**
- Modify: `python-scripts/expense-tracker/config.py` (add `ALERT_SENDERS`)
- Modify: `python-scripts/expense-tracker/gmail_client.py` (query + `is_alert` tag)
- Modify: `python-scripts/expense-tracker/expense_scanner.py` (system prompt, carry `is_alert`)
- Modify: `python-scripts/expense-tracker/main.py` (dedup pass, `--dry-run`)
- Create: `python-scripts/expense-tracker/tests/test_scanner.py`
- Modify: `python-scripts/expense-tracker/README.md`

**Interfaces:**
- Produces: `main.dedupe_bank_alerts(expenses) -> list` (drops alert-source expenses that duplicate a non-alert expense: same amount, dates within 2 days). Expense dicts gain optional `"is_alert": True`. `main.py` accepts `--dry-run` (prints, writes nothing). Task 3 consumes the final deduped `expenses` list.

- [ ] **Step 1: Write the failing tests** (`tests/test_scanner.py`):

```python
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
    for old in ["Streaming", "Transport", "Health & Wellness", "Shopping"]:
        assert old + " " not in _SYSTEM_PROMPT.split("category: one of")[1].split("Venmo")[0]
    for new in ["BJJ & Kickboxing", "Investments", "Misc"]:
        assert new in _SYSTEM_PROMPT

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
```

- [ ] **Step 2:** Run: `cd python-scripts/expense-tracker && python -m pytest tests/ -v` — Expected: FAIL (`build_query`, `ALERT_SENDERS`, `dedupe_bank_alerts` don't exist).
- [ ] **Step 3: Implement.**

`config.py` — append:

```python
# Bank per-transaction alert emails (card swipes with no vendor receipt email).
# PrimeSouth sender domain is a best guess until Gray forwards a real alert —
# update this list when the first alert lands. Alerts are deduped against
# vendor receipts in main.dedupe_bank_alerts.
ALERT_SENDERS = [
    "primesouth.com",
    "secure.primesouth.com",
]
```

`gmail_client.py` — extract the query into a function and tag alert emails. Replace the `query = (...)` literal inside `fetch_personal_expense_emails` with a call to `build_query(days)`, where `build_query` is the old literal plus alert senders spliced in before the closing paren:

```python
def build_query(days):
    alert_from = " ".join(f"OR from:{s}" for s in ALERT_SENDERS)
    return (
        f"newer_than:{days}d "
        "(subject:receipt OR subject:\"order confirmation\" ..."   # ← existing literal UNCHANGED
        f"... OR from:bestbuy.com {alert_from}) "
        "-from:me"
    )
```

(import `ALERT_SENDERS` from config). In `_parse_email`, add after the `body` line:

```python
sender = headers.get("From", "").lower()
is_alert = any(s in sender for s in ALERT_SENDERS)
```

and include `"is_alert": is_alert` in the returned dict.

`expense_scanner.py` — two prompt edits: (a) replace the nine-category block in `_SYSTEM_PROMPT` with the seven PERSONAL_CATEGORIES (Groceries / Dining Out / Software & Tools / Utilities / Investments / BJJ & Kickboxing / Misc — reuse the existing per-category hint text, folding Streaming→Software & Tools hint removed, old Streaming/Transport/Health/Shopping examples land under Misc); (b) add a bank-alert section after the Venmo rules:

```
Bank transaction alert rules (sender is the bank, e.g. PrimeSouth):
- "Your card was charged $X at MERCHANT" / "A transaction of $X was made at MERCHANT" → IT IS AN EXPENSE. vendor = the merchant name (clean it up: "DOORDASH*NYC" → "DoorDash"), never the bank.
- Deposit / payment received / balance / low-balance alerts → SKIP (return null).
- ATM withdrawals → category "Misc".
```

In `scan_expenses`, carry the flag: inside the `if result:` block add `if email.get("is_alert"): expense["is_alert"] = True` (and same for the cached-return path — cached entries already stored it or not).

`main.py` — add after `_apply_category_override`:

```python
def dedupe_bank_alerts(expenses):
    """Drop bank-alert expenses that duplicate a vendor receipt (same amount, within 2 days)."""
    from datetime import date as _date
    def _d(s):
        y, m, dd = s.split("-"); return _date(int(y), int(m), int(dd))
    receipts = [e for e in expenses if not e.get("is_alert")]
    out = list(receipts)
    for a in (e for e in expenses if e.get("is_alert")):
        dup = any(
            r["amount"] == a["amount"] and abs((_d(r["date"]) - _d(a["date"])).days) <= 2
            for r in receipts
        )
        if not dup:
            out.append(a)
    return out
```

In `main()`: apply `expenses = dedupe_bank_alerts(expenses)` right after the category-override loop, printing how many alerts were dropped. Add argparse-free flag handling at the top of `main()`: `dry_run = "--dry-run" in sys.argv` (import sys); when `dry_run`, print the expense summary but skip `write_expenses_json` (and later, Task 3's Firestore write), printing `DRY RUN — nothing written.`

- [ ] **Step 4:** Run: `python -m pytest tests/ -v` — Expected: 7 passed. Then run the full Phase 1 suite untouched-check: `python web-apps/payday-checklist/tests/test_payday.py` — Expected: 46 passed.
- [ ] **Step 5:** Update `README.md` (categories note, ALERT_SENDERS, dedup, --dry-run) and commit: `git commit -m "expense-tracker: 7-category prompt, bank-alert parsing + dedup, --dry-run"`

---

### Task 3: Scanner — Firestore writer (create-only, optional)

**Files:**
- Create: `python-scripts/expense-tracker/firestore_writer.py`
- Modify: `python-scripts/expense-tracker/main.py`, `requirements.txt`, `README.md`
- Test: `python-scripts/expense-tracker/tests/test_firestore_writer.py`

**Interfaces:**
- Produces: `firestore_writer.write_expenses(expenses, client=None) -> int` (count actually created). `firestore_writer.get_client() -> client|None` (None when `FIREBASE_SERVICE_ACCOUNT` env absent). Doc path: `households/gray/transactions/{email_id}`.

- [ ] **Step 1: Write the failing tests** (`tests/test_firestore_writer.py`):

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

import firestore_writer


class FakeDoc:
    def __init__(self, store, path): self.store, self.path = store, path
    def create(self, data):
        if self.path in self.store:
            raise firestore_writer.AlreadyExists("exists")
        self.store[self.path] = data

class FakeClient:
    def __init__(self): self.store = {}
    def document(self, path): return FakeDoc(self.store, path)


def _exp(eid="e1", **kw):
    d = {"email_id": eid, "date": "2026-07-07", "vendor": "Bodega", "amount": 12.0, "category": "Misc"}
    d.update(kw); return d

def test_writes_new_expense():
    c = FakeClient()
    n = firestore_writer.write_expenses([_exp()], client=c)
    assert n == 1
    doc = c.store["households/gray/transactions/e1"]
    assert doc["vendor"] == "Bodega" and doc["deleted"] is False
    assert doc["month"] == "2026-07" and doc["source"] == "gmail"
    assert "is_alert" not in doc  # internal flag not persisted

def test_skips_existing_doc():
    c = FakeClient()
    firestore_writer.write_expenses([_exp()], client=c)
    n = firestore_writer.write_expenses([_exp(vendor="Changed")], client=c)
    assert n == 0
    assert c.store["households/gray/transactions/e1"]["vendor"] == "Bodega"  # never overwritten

def test_no_env_returns_none_client():
    os.environ.pop("FIREBASE_SERVICE_ACCOUNT", None)
    assert firestore_writer.get_client() is None
```

- [ ] **Step 2:** Run: `python -m pytest tests/test_firestore_writer.py -v` — Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `firestore_writer.py`:

```python
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
```

`main.py` — in `main()`, after `write_expenses_json(...)` (both guarded by `dry_run`):

```python
    if dry_run:
        print("\nDRY RUN — nothing written.")
        return
    write_expenses_json(expenses, current_month)
    import firestore_writer
    fs_client = firestore_writer.get_client()
    if fs_client:
        created = firestore_writer.write_expenses(expenses, client=fs_client)
        print(f"Firestore: {created} new expense(s) written to {firestore_writer.ROOT}.")
    else:
        print("Firestore: skipped (FIREBASE_SERVICE_ACCOUNT not set).")
```

`requirements.txt` — add `firebase-admin`.

- [ ] **Step 4:** Run: `python -m pytest tests/ -v` — Expected: 10 passed. Live sanity: `python main.py --dry-run` — Expected: normal scan output ending `DRY RUN — nothing written.` (uses the local Gmail token; a few cents of Haiku only if new emails exist).
- [ ] **Step 5:** Update README (Firestore section), commit: `git commit -m "expense-tracker: optional Firestore writer (create-only, households/gray)"`

---

### Task 4: Workflow — 30-minute cron + concurrency + optional secret

**Files:**
- Modify: `.github/workflows/expense-sync.yml`

- [ ] **Step 1:** Edit the workflow: replace the `schedule` block cron with `"*/30 * * * *"` (delete the EDT comment — no longer time-of-day dependent); add below `permissions:`:

```yaml
concurrency:
  group: expense-sync
  cancel-in-progress: false
```

and add to the "Run expense scanner" step's `env:`: `FIREBASE_SERVICE_ACCOUNT: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}` (an unset secret yields empty string → writer stays inert).

- [ ] **Step 2:** Validate YAML: `python -c "import yaml; yaml.safe_load(open('.github/workflows/expense-sync.yml'))"` — Expected: no output.
- [ ] **Step 3:** Commit: `git commit -m "expense-sync: 30-min cadence, concurrency guard, optional Firestore secret"`

---

### Task 5: App — vendor Firebase SDK, config flag, SW v3 (inert deploy)

**Files:**
- Create: `web-apps/payday-checklist/lib/firebase-app-compat.js`, `lib/firebase-auth-compat.js`, `lib/firebase-firestore-compat.js`
- Create: `web-apps/payday-checklist/firebase-config.js`
- Modify: `web-apps/payday-checklist/index.html` (script tags only), `sw.js`

- [ ] **Step 1:** Download the compat SDK (try current major first; on 404 fall back):

```bash
cd "web-apps/payday-checklist" && mkdir -p lib
for f in firebase-app-compat.js firebase-auth-compat.js firebase-firestore-compat.js; do
  curl -fsSL "https://www.gstatic.com/firebasejs/12.1.0/$f" -o "lib/$f" \
    || curl -fsSL "https://www.gstatic.com/firebasejs/10.14.1/$f" -o "lib/$f"
done
ls -la lib/
```

Expected: three non-empty .js files.

- [ ] **Step 2:** Create `firebase-config.js`:

```js
// Firebase web config — intentionally public (security lives in firestore.rules).
// null = sync disabled, app runs local-only exactly like Phase 1.
// After creating the Firebase project, replace null with the config object
// from Console → Project settings → Your apps → Web app.
window.FIREBASE_CONFIG = null;
```

- [ ] **Step 3:** In `index.html` `<head>` after the `<title>` block add:

```html
  <script src="./lib/firebase-app-compat.js" defer></script>
  <script src="./lib/firebase-auth-compat.js" defer></script>
  <script src="./lib/firebase-firestore-compat.js" defer></script>
  <script src="./firebase-config.js" defer></script>
```

(`sync.js` is added in Task 6.) In `sw.js`: `CACHE_NAME = 'payday-checklist-v3'`, and extend PRECACHE with `'./firebase-config.js', './lib/firebase-app-compat.js', './lib/firebase-auth-compat.js', './lib/firebase-firestore-compat.js'`.

- [ ] **Step 4:** Run: `python web-apps/payday-checklist/tests/test_payday.py` — Expected: 46 passed (SDK loads, does nothing).
- [ ] **Step 5:** Commit: `git commit -m "payday: vendor Firebase compat SDK + config flag + SW v3 (sync still inert)"`

---

### Task 6: App — sync engine (`sync.js`) + IDB hooks + sync UI

The heart of the build. `index.html` mutation points get `sid`/`updatedAt`/tombstones; `sync.js` owns mirroring + snapshot application.

**Files:**
- Create: `web-apps/payday-checklist/sync.js`
- Modify: `web-apps/payday-checklist/index.html`
- Modify: `web-apps/payday-checklist/sw.js` (add `./sync.js` to PRECACHE)

**Interfaces:**
- Consumes: `window.FIREBASE_CONFIG` (Task 5), globals from index.html: `db, TXN_CACHE, OVERRIDES, refreshExpenseDisplays(), getSetting/setSetting, addTransaction, getAllTransactions, showToast`.
- Produces (used by index.html): `Sync.init()`, `Sync.onLocalTxn(txn)`, `Sync.onLocalTxnDelete(txn)`, `Sync.onLocalSetting(key, value)`, `Sync.onLocalHistory(entry)`, `Sync.onLocalHistoryDelete(id)`, `Sync.signIn()`, `Sync.signOut()`.
- Produces (used by tests): fake backend hook `window.__SYNC_BACKEND` — if defined, `Sync.init()` uses it instead of Firebase and treats the user as signed in.

**Backend interface (both FirebaseBackend and the test fake implement):**

```js
// set(path, data)        -> Promise    path like 'transactions/abc123'
// subscribe(cb)          -> unsubscribe   cb(docs) with docs = {path: data, ...} (full state, called on every change)
// signIn() / signOut()   -> Promise
// onAuth(cb)             -> cb(user|null)
```

- [ ] **Step 1:** Write `sync.js`:

```js
'use strict';
// sync.js — Payday Checklist cross-device sync engine.
// Local IndexedDB stays the UI's store; this mirrors mutations to a backend
// (Firestore in production, window.__SYNC_BACKEND fake in tests) and applies
// remote snapshots with last-write-wins by updated_at + tombstone deletes.

const Sync = (() => {
  const ROOT = 'households/gray';
  const ALLOWED_EMAIL = 'graydavis33@gmail.com';
  const SETTING_KEYS = ['income', 'allocations', 'budgets', 'fund', 'ring', 'steps', 'notes', 'overrides', 'dismissed_gmail'];

  let backend = null;
  let active = false;        // signed in + subscribed
  let applyingRemote = false; // guard: remote application must not re-mirror

  function uuid() {
    return crypto.randomUUID ? crypto.randomUUID()
      : 'xxxxxxxxyxxx'.replace(/[xy]/g, c => (Math.random() * 16 | 0).toString(16));
  }

  // ── status UI ──
  function setStatus(text) {
    const el = document.getElementById('cloud-sync-status');
    if (el) el.textContent = text;
    const btn = document.getElementById('cloud-sync-btn');
    if (btn) btn.textContent = active ? 'sign out' : 'sign in';
  }

  // ── FirebaseBackend ──
  function makeFirebaseBackend(config) {
    firebase.initializeApp(config);
    const auth = firebase.auth();
    const fs = firebase.firestore();
    fs.enablePersistence({ synchronizeTabs: true }).catch(() => {});
    return {
      set: (path, data) => fs.doc(ROOT + '/' + path).set(data),
      subscribe(cb) {
        const unsubs = ['transactions', 'settings', 'history'].map(col =>
          fs.collection(ROOT + '/' + col).onSnapshot(snap => {
            const docs = {};
            snap.forEach(d => { docs[col + '/' + d.id] = d.data(); });
            cb(docs, col);
          })
        );
        return () => unsubs.forEach(u => u());
      },
      async signIn() {
        const provider = new firebase.auth.GoogleAuthProvider();
        try { await auth.signInWithPopup(provider); }
        catch (e) { await auth.signInWithRedirect(provider); }
      },
      signOut: () => auth.signOut(),
      onAuth(cb) {
        auth.onAuthStateChanged(u => {
          if (u && u.email !== ALLOWED_EMAIL) { auth.signOut(); cb(null); return; }
          cb(u);
        });
      }
    };
  }

  // ── local application of remote docs ──
  async function applyRemote(docs, colHint) {
    applyingRemote = true;
    try {
      let txnChanged = false, settingsChanged = false;
      const bySid = {};
      TXN_CACHE.forEach(t => { if (t.sid) bySid[t.sid] = t; });
      const allLocal = await getAllTransactions();
      const allBySid = {};
      allLocal.forEach(t => { if (t.sid) allBySid[t.sid] = t; });

      for (const [path, data] of Object.entries(docs)) {
        const [col, id] = [path.slice(0, path.indexOf('/')), path.slice(path.indexOf('/') + 1)];
        if (col === 'transactions') {
          const local = allBySid[id];
          if (local && (local.updatedAt || 0) >= (data.updated_at || 0)) continue;
          const rec = {
            ...(local || {}),
            sid: id, vendor: data.vendor, amount: data.amount, category: data.category,
            date: data.date, month: data.month, note: data.note || '',
            source: data.source || 'manual', deleted: !!data.deleted,
            createdAt: local ? local.createdAt : new Date(data.createdAt || Date.now()).toISOString(),
            updatedAt: data.updated_at || 0
          };
          if (data.email_id) rec.email_id = data.email_id;
          const newId = await addTransaction(rec);   // put() — updates when rec.id exists, adds otherwise
          if (rec.id == null) rec.id = newId;
          allBySid[id] = rec;
          txnChanged = true;
        } else if (col === 'settings') {
          if (!SETTING_KEYS.includes(id)) continue;
          const meta = await getSetting('_syncmeta_' + id, 0);
          if (meta >= (data.updated_at || 0)) continue;
          await setSetting(id, data.value);            // hook skips mirroring (applyingRemote)
          await setSetting('_syncmeta_' + id, data.updated_at || 0);
          settingsChanged = true;
        } else if (col === 'history') {
          const data2 = data;
          if (data2.deleted) { await deleteHistory(Number(id)); }
          else { await putHistory(data2.entry); }
        }
      }

      if (txnChanged) {
        TXN_CACHE = (await getAllTransactions()).filter(t => !t.deleted);
        refreshExpenseDisplays();
      }
      if (settingsChanged) await reloadSettingsIntoUI();
      if (txnChanged || settingsChanged) setStatus('✓ synced');
    } finally {
      applyingRemote = false;
    }
  }

  // Re-read synced settings into the live UI (mirror of init()'s load block)
  async function reloadSettingsIntoUI() {
    const income = await getSetting('income', { biweekly: 3250, taxPct: 30 });
    const allocs = await getSetting('allocations', { rent: 1900, loans: 1000, ef: 400, ring: 200 });
    const budgets = await getSetting('budgets', null);
    const fund = await getSetting('fund', { balance: '', goal: 12000 });
    const ring = await getSetting('ring', { balance: '', goal: 10000 });
    const steps = await getSetting('steps', {});
    document.getElementById('paycheck-amount').value = income.biweekly;
    document.getElementById('tax-percent').value = income.taxPct;
    document.getElementById('alloc-rent').value = allocs.rent;
    document.getElementById('alloc-loans').value = allocs.loans;
    document.getElementById('alloc-ef').value = allocs.ef;
    document.getElementById('alloc-ring').value = allocs.ring;
    document.getElementById('fund-balance').value = fund.balance;
    document.getElementById('fund-goal').value = fund.goal;
    document.getElementById('ring-balance').value = ring.balance;
    document.getElementById('ring-goal').value = ring.goal;
    document.getElementById('notes').value = await getSetting('notes', '');
    if (budgets && budgets.length === CATEGORIES.length) {
      BUDGETS = [...budgets];
      BUDGETS.forEach((b, i) => document.getElementById('budget-' + i).value = b);
    }
    OVERRIDES = await getSetting('overrides', {});
    for (let i = 0; i < STEP_NAMES.length; i++)
      document.getElementById('step-' + i).classList.toggle('done', !!steps[i]);
    await updateAllocations(false);
    await updateFund(false);
    await updateRing(false);
    refreshExpenseDisplays();
  }

  // ── mirroring local → cloud ──
  function txnDoc(t) {
    return {
      vendor: t.vendor, amount: t.amount, category: t.category, date: t.date,
      month: t.month, note: t.note || '', source: t.source || 'manual',
      ...(t.email_id ? { email_id: t.email_id } : {}),
      deleted: !!t.deleted,
      createdAt: Date.parse(t.createdAt || '') || Date.now(),
      updated_at: t.updatedAt || Date.now()
    };
  }

  async function onLocalTxn(t) {
    if (!active || applyingRemote) return;
    backend.set('transactions/' + t.sid, txnDoc(t)).catch(() => setStatus('⚠ sync error'));
  }
  async function onLocalTxnDelete(t) { return onLocalTxn(t); }   // tombstone rides the same doc
  async function onLocalSetting(key, value) {
    if (!active || applyingRemote || !SETTING_KEYS.includes(key)) return;
    const now = Date.now();
    await setSetting('_syncmeta_' + key, now);
    backend.set('settings/' + key, { value, updated_at: now }).catch(() => setStatus('⚠ sync error'));
  }
  async function onLocalHistory(entry) {
    if (!active || applyingRemote) return;
    backend.set('history/' + entry.id, { entry, deleted: false, updated_at: Date.now() }).catch(() => {});
  }
  async function onLocalHistoryDelete(id) {
    if (!active || applyingRemote) return;
    backend.set('history/' + id, { entry: null, deleted: true, updated_at: Date.now() }).catch(() => {});
  }

  // ── first-sign-in migration: push everything local up ──
  async function migrateUp() {
    const done = await getSetting('sync_migrated', false);
    if (done) return;
    const txns = await getAllTransactions();
    for (const t of txns) {
      if (!t.sid) {
        t.sid = t.email_id || uuid();
        t.updatedAt = Date.now();
        await addTransaction(t);
      }
      await backend.set('transactions/' + t.sid, txnDoc(t));
    }
    TXN_CACHE = (await getAllTransactions()).filter(t => !t.deleted);
    for (const key of SETTING_KEYS) {
      const v = await getSetting(key);
      if (v != null) {
        const now = Date.now();
        await setSetting('_syncmeta_' + key, now);
        await backend.set('settings/' + key, { value: v, updated_at: now });
      }
    }
    for (const h of await getAllHistory())
      await backend.set('history/' + h.id, { entry: h, deleted: false, updated_at: Date.now() });
    await setSetting('sync_migrated', true);
  }

  // ── lifecycle ──
  let unsubscribe = null;

  async function onUser(user) {
    if (user) {
      active = true;
      setStatus('syncing…');
      await migrateUp();
      unsubscribe = backend.subscribe(docs => { applyRemote(docs); });
      setStatus('✓ synced');
    } else {
      active = false;
      if (unsubscribe) { unsubscribe(); unsubscribe = null; }
      setStatus(backend ? 'sync off — sign in' : '');
    }
  }

  function init() {
    if (window.__SYNC_BACKEND) {
      backend = window.__SYNC_BACKEND;
      backend.onAuth(onUser);
      return;
    }
    if (!window.FIREBASE_CONFIG || typeof firebase === 'undefined') {
      const row = document.getElementById('cloud-sync-row');
      if (row) row.style.display = 'none';
      return;
    }
    backend = makeFirebaseBackend(window.FIREBASE_CONFIG);
    backend.onAuth(onUser);
  }

  return {
    init, onLocalTxn, onLocalTxnDelete, onLocalSetting, onLocalHistory, onLocalHistoryDelete,
    signIn: () => backend && backend.signIn(),
    signOut: () => backend && backend.signOut(),
    toggle: () => (active ? Sync.signOut() : Sync.signIn())
  };
})();
```

- [ ] **Step 2: index.html hook edits** (each is a small surgical change):

1. `setSetting(key, value)` — after the put resolves, add `Sync.onLocalSetting(key, value);` (fire-and-forget). Skip when key starts with `_syncmeta_` or is `sync_migrated`/`migrated_v1`: wrap as `if (!key.startsWith('_syncmeta_') && key !== 'sync_migrated' && key !== 'migrated_v1') Sync.onLocalSetting(key, value);`
2. `submitAddExpense()` — before `await addTransaction(txn)` add `txn.sid = uuidSid(); txn.updatedAt = Date.now();` where a tiny helper goes next to `escapeHtml`: `function uuidSid() { return crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2); }`. After `TXN_CACHE.push(txn)` add `Sync.onLocalTxn(txn);`
3. `loadGmailExpenses()` — in the txn literal add `sid: exp.email_id, updatedAt: Date.now(),` and after `TXN_CACHE.push(txn)` add `Sync.onLocalTxn(txn);`
4. `removeTxn(id)` — replace `await deleteTransaction(id);` with tombstone semantics:

```js
  txn.deleted = true;
  txn.updatedAt = Date.now();
  if (!txn.sid) txn.sid = txn.email_id || uuidSid();
  await addTransaction(txn);        // put() keeps the tombstone row
  Sync.onLocalTxnDelete(txn);
```

(keep the existing `dismissed_gmail` block — still needed for the expenses.json path until cutover; keep `TXN_CACHE = TXN_CACHE.filter(...)`).
5. `resetExpenses()` — same replacement inside its loop: tombstone each txn (`t.deleted = true; t.updatedAt = Date.now(); if (!t.sid) t.sid = t.email_id || uuidSid(); await addTransaction(t); Sync.onLocalTxnDelete(t);`) instead of `deleteTransaction(t.id)`.
6. `submitPayday()` — after `await putHistory(entry)` add `Sync.onLocalHistory(entry);`
7. `removeHistoryEntry(id)` — after `await deleteHistory(id)` add `Sync.onLocalHistoryDelete(id);`
8. `init()` — change the TXN_CACHE load line to `TXN_CACHE = (await getAllTransactions()).filter(t => !t.deleted);` and add `Sync.init();` immediately after `loadGmailExpenses();`
9. Sync status row — in the `gm-card` that holds `sync-badge`, add below it:

```html
          <div class="sync-badge" id="cloud-sync-row">
            <span id="cloud-sync-status"></span>
            <a id="cloud-sync-btn" onclick="Sync.toggle()">sign in</a>
          </div>
```

10. `<script src="./sync.js" defer></script>` after the firebase-config.js tag; add `'./sync.js'` to sw.js PRECACHE.
11. `exportCSV()` — no change (tombstoned rows export with their `deleted` flag absent from the CSV columns; acceptable: import regenerates sids and tombstones are not round-tripped — they exist in the cloud).

**Ordering note:** `sync.js` references index.html globals at *call* time only, and index.html calls `Sync.*` at *runtime* only — `defer` order (`sync.js` before the inline script's DOMContentLoaded init) is safe.

- [ ] **Step 3:** Run: `python web-apps/payday-checklist/tests/test_payday.py` — Expected: 46 passed (config null → `Sync.init()` hides the row and returns; hooks are no-ops with `active === false`).
- [ ] **Step 4:** Commit: `git commit -m "payday: sync engine + IDB tombstones/sids + sync UI (inert until configured)"`

---### Task 7: Sync e2e tests — two devices against the fake backend

**Files:**
- Create: `web-apps/payday-checklist/tests/test_sync.py`

The fake backend is injected per-context via `add_init_script` and speaks to `serve.py`'s `/fake/*` store — two browser contexts = two devices sharing one fake cloud, polling every 250ms.

- [ ] **Step 1:** Write `test_sync.py`:

```python
"""Sync e2e — two browser contexts share the /fake/* backend (simulates iPhone + Windows)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import start_server
import urllib.request

PORT = 4791
URL = f"http://localhost:{PORT}/payday-checklist/index.html"
httpd = start_server(PORT)

FAKE_BACKEND_JS = """
window.__SYNC_BACKEND = (() => {
  let authCb = null, subCb = null, lastRev = -1, timer = null;
  async function poll() {
    const r = await fetch('/fake/state').then(r => r.json()).catch(() => null);
    if (r && r.rev !== lastRev) { lastRev = r.rev; if (subCb) subCb(r.docs); }
  }
  return {
    set: (path, data) => fetch('/fake/set', { method: 'POST', body: JSON.stringify({ path, data }) }),
    subscribe(cb) { subCb = cb; poll(); timer = setInterval(poll, 250); return () => clearInterval(timer); },
    signIn() { authCb({ email: 'graydavis33@gmail.com' }); return Promise.resolve(); },
    signOut() { authCb(null); return Promise.resolve(); },
    onAuth(cb) { authCb = cb; setTimeout(() => cb({ email: 'graydavis33@gmail.com' }), 50); }
  };
})();
"""

passed, failed = [], []
def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {'' if cond else detail}")

def reset_fake():
    urllib.request.urlopen(urllib.request.Request(f"http://localhost:{PORT}/fake/reset", method="POST"), b"{}")

from playwright.sync_api import sync_playwright

def new_device(browser):
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    pg.add_init_script(FAKE_BACKEND_JS)
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_selector("body[data-ready='1']", timeout=10000)
    pg.wait_for_timeout(600)   # onAuth fires + migration runs
    return ctx, pg

def add_expense(pg, vendor, amount):
    pg.click(".fab")
    pg.fill("#add-vendor", vendor)
    pg.fill("#add-amount", str(amount))
    pg.click(".add-modal .gm-btn-primary")
    pg.wait_for_timeout(200)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ══ 1. add on A → appears on B ══
    print("\n[1] Cross-device add")
    reset_fake()
    ctxA, A = new_device(browser)
    ctxB, B = new_device(browser)
    add_expense(A, "Sync Coffee", 7.50)
    B.wait_for_timeout(900)
    check("expense from A appears on B", "Sync Coffee" in (B.text_content("#txn-list-6") or B.content()))

    # ══ 2. dismiss on B → vanishes on A ══
    print("\n[2] Cross-device delete (tombstone)")
    B.click("#txn-toggle-6")
    B.click("#txn-list-6 .txn-delete")
    A.wait_for_timeout(900)
    check("deleted on B vanishes on A", "Sync Coffee" not in (A.text_content("#txn-list-6") or ""))
    ctxA.close(); ctxB.close()

    # ══ 3. offline queue: A offline → add → online → B sees it ══
    print("\n[3] Offline queue")
    reset_fake()
    ctxA, A = new_device(browser)
    ctxB, B = new_device(browser)
    ctxA.set_offline(True)
    add_expense(A, "Offline Bagel", 4.25)
    check("offline add shows locally on A", "4.25" == A.input_value("#spent-input-6"))
    B.wait_for_timeout(700)
    check("B does NOT see it while A offline", "Offline Bagel" not in B.content())
    ctxA.set_offline(False)
    A.wait_for_timeout(500)
    # our engine mirrors at write time; after reconnect the fetch retries on next local event —
    # re-trigger by touching the txn (fake backend has no queue, so verify via A re-open)
    A.reload(); A.wait_for_selector("body[data-ready='1']"); A.wait_for_timeout(800)
    B.wait_for_timeout(900)
    check("after A reconnects, B sees the expense", "Offline Bagel" in B.content())
    ctxA.close(); ctxB.close()

    # ══ 4. LWW conflict on a setting ══
    print("\n[4] Last-write-wins on settings")
    reset_fake()
    ctxA, A = new_device(browser)
    ctxB, B = new_device(browser)
    A.fill("#alloc-rent", "2100"); A.wait_for_timeout(300)
    B.fill("#alloc-rent", "2200"); B.wait_for_timeout(900)   # B writes later → should win
    A.wait_for_timeout(900)
    check("later write (B=2200) wins on A", A.input_value("#alloc-rent") == "2200", A.input_value("#alloc-rent"))
    ctxA.close(); ctxB.close()

    # ══ 5. first-sign-in migration ══
    print("\n[5] Migration uploads pre-existing local data")
    reset_fake()
    ctxA, A = new_device(browser)          # device A: has data BEFORE fake-cloud reset? simulate:
    add_expense(A, "Legacy Groceries", 55.00)
    A.wait_for_timeout(400)
    ctxB, B = new_device(browser)          # fresh device signs in later
    B.wait_for_timeout(1200)
    check("fresh device receives migrated data", "Legacy Groceries" in B.content())
    ctxA.close(); ctxB.close()

    browser.close()

print(f"\n{'='*40}\n{len(passed)} passed, {len(failed)} failed")
if failed: print("FAILED:", failed)
sys.exit(1 if failed else 0)
```

- [ ] **Step 2:** Run: `python web-apps/payday-checklist/tests/test_sync.py` — Expected: FAIL initially only if Task 6 has bugs; iterate on `sync.js`/hooks until **6 passed, 0 failed**. Note: test [3] documents a real engine property — writes made while offline mirror on next page load via migration/re-put, and in production Firestore's own offline queue handles it natively (the fake has no queue). If [3]'s reconnect semantics can't pass with the fake, replace the reload with an explicit re-put and keep the assertion; do NOT weaken assertions 1/2/4/5.
- [ ] **Step 3:** Run the Phase 1 suite again: `python web-apps/payday-checklist/tests/test_payday.py` — Expected: 46 passed.
- [ ] **Step 4:** Commit: `git commit -m "payday: sync e2e — cross-device add/delete/offline/LWW/migration vs fake backend"`

---

### Task 8: Firestore rules + Gray's handoff doc

**Files:**
- Create: `web-apps/payday-checklist/firestore.rules`
- Create: `web-apps/payday-checklist/PHASE2-HANDOFF.md`

- [ ] **Step 1:** `firestore.rules`:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /households/gray/{document=**} {
      allow read, write: if request.auth != null
        && request.auth.token.email == 'graydavis33@gmail.com'
        && request.auth.token.email_verified == true;
    }
  }
}
```

- [ ] **Step 2:** `PHASE2-HANDOFF.md` — exact console steps, numbered: (1) console.firebase.google.com → Add project (name `payday-checklist`, Analytics off). (2) Build → Authentication → Get started → Sign-in method → Google → Enable. (3) Build → Firestore Database → Create (production mode, nam5). (4) Rules tab → paste `firestore.rules` → Publish. (5) Project settings → Your apps → Web (`</>`) → register `payday` → copy the `firebaseConfig = {...}` object → paste into `web-apps/payday-checklist/firebase-config.js` replacing `null` → commit+push (or tell Claude). (6) Authentication → Settings → Authorized domains → add `graydavis33.github.io`. (7) Project settings → Service accounts → Generate new private key → GitHub repo → Settings → Secrets → Actions → new secret `FIREBASE_SERVICE_ACCOUNT` → paste the JSON. (8) PrimeSouth app → card alerts → enable per-transaction alerts, delivery EMAIL, threshold $0/all → forward one alert to Claude next session so ALERT_SENDERS + the parser get locked to the real format. (9) Live smoke test list (from the spec §Testing). Include: "iOS note — if Google sign-in fails inside the installed PWA, sign in once in Safari first, then reinstall from Share → Add to Home Screen; popup vs redirect is auto-handled."
- [ ] **Step 3:** Commit: `git commit -m "payday: firestore rules + Phase 2 handoff checklist for Gray"`

---

### Task 9: Docs + logs sweep (same-session hygiene)

**Files:**
- Modify: `python-scripts/expense-tracker/README.md` (if anything shifted in Tasks 2-3 review)
- Modify: `web-apps/payday-checklist/PAYDAY-SPEC-2026-07.md` (add a one-line Phase 2 pointer to the new spec)
- Modify: `decisions/log.md` (append: Firebase over VPS + alert-emails over Plaid, with the why)
- Modify: `context/priorities.md` (Payday v2 entry: Phase 2 built, pending Gray's handoff steps)

- [ ] **Step 1:** Make the four doc edits.
- [ ] **Step 2:** Full verification: both e2e suites + scanner pytest, all green. Run: `python web-apps/payday-checklist/tests/test_payday.py && python web-apps/payday-checklist/tests/test_sync.py && cd python-scripts/expense-tracker && python -m pytest tests/ -v`
- [ ] **Step 3:** Commit: `git commit -m "payday phase 2: docs, decisions log, priorities"`

---

## Self-Review Notes

- Spec §"scanner keeps expenses.json when secret present" → Task 3 writes both paths ✓; cutover is explicitly post-smoke (Gray handoff step 9) ✓
- Spec §dismissed_gmail retirement → deferred to cutover; both mechanisms coexist safely because scanner create-only + tombstones make resurrection impossible ✓
- Type check: `sid`/`updatedAt` (camelCase, local IDB) vs `updated_at` (Firestore docs) — intentional, mapped only inside `txnDoc()`/`applyRemote()` ✓
- `addTransaction` uses IDB `put()` so it doubles as update — relied on by tombstones + applyRemote ✓ (keyPath `id` autoIncrement: put() with existing id updates, without id adds ✓)
- Fake backend `subscribe` returns full state each poll — matches FirebaseBackend per-collection snapshots closely enough (applyRemote is idempotent) ✓
