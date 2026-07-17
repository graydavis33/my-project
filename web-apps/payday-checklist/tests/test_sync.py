"""Sync e2e — two browser contexts share the /fake/* backend (simulates iPhone + Windows).

The fake backend mimics Firestore semantics the engine relies on:
- set() resolves immediately and queues the write (Firestore's offline queue)
- queued writes flush on the next poll tick once the network is back
- subscribe() delivers the full doc state on every change
"""
import sys, os

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import start_server
import urllib.request

PORT = 4791
URL = f"http://localhost:{PORT}/payday-checklist/index.html"
httpd = start_server(PORT)

FAKE_BACKEND_JS = """
window.__SYNC_BACKEND = (() => {
  let authCb = null, subCb = null, lastRev = -1, timer = null;
  const outbox = [];
  async function flush() {
    while (outbox.length) {
      const item = outbox[0];
      try {
        await fetch('/fake/set', { method: 'POST', body: JSON.stringify(item) });
        outbox.shift();
      } catch (e) { return; }   // still offline — retry next tick
    }
  }
  async function poll() {
    await flush();
    try {
      const r = await fetch('/fake/state', { cache: 'no-store' }).then(r => r.json());
      if (r.rev !== lastRev) { lastRev = r.rev; if (subCb) subCb(r.docs); }
    } catch (e) { /* offline */ }
  }
  return {
    set(path, data) { outbox.push({ path, data }); flush(); return Promise.resolve(); },
    subscribe(cb) { subCb = cb; poll(); timer = setInterval(poll, 250); return () => clearInterval(timer); },
    signIn() { authCb({ email: 'graydavis33@gmail.com' }); return Promise.resolve(); },
    signOut() { authCb(null); return Promise.resolve(); },
    onAuth(cb) { authCb = cb; setTimeout(() => cb({ email: 'graydavis33@gmail.com' }), 50); }
  };
})();
"""

passed, failed = [], []

def check(name, cond, detail=""):
    if cond:
        passed.append(name)
        print(f"  PASS  {name}")
    else:
        failed.append((name, detail))
        print(f"  FAIL  {name}  {detail}")

def reset_fake():
    urllib.request.urlopen(urllib.request.Request(f"http://localhost:{PORT}/fake/reset", method="POST"), b"{}")

from playwright.sync_api import sync_playwright

def new_device(browser, with_backend=True):
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    pg = new_page(ctx, with_backend)
    return ctx, pg

def new_page(ctx, with_backend=True):
    pg = ctx.new_page()
    if with_backend:
        pg.add_init_script(FAKE_BACKEND_JS)
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL)
    pg.wait_for_selector("body[data-ready='1']", timeout=10000)
    pg.wait_for_timeout(700)   # onAuth fires + migration runs
    return pg

def add_expense(pg, vendor, amount):
    pg.click(".fab")
    pg.fill("#add-vendor", vendor)
    pg.fill("#add-amount", str(amount))
    pg.click(".add-modal .gm-btn-primary")
    pg.wait_for_timeout(250)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ══ 1. add on A → appears on B ══
    print("\n[1] Cross-device add")
    reset_fake()
    ctxA, A = new_device(browser)
    ctxB, B = new_device(browser)
    add_expense(A, "Zzyzx Trinket", 7.50)     # keyword-neutral → Misc (index 6)
    B.wait_for_timeout(1000)
    got = B.text_content("#txn-list-5") or ""
    check("expense from A appears on B", "Zzyzx Trinket" in got, got[:120])
    check("B sync status shows synced", "synced" in (B.text_content("#cloud-sync-status") or ""),
          B.text_content("#cloud-sync-status"))

    # ══ 2. dismiss on B → vanishes on A ══
    print("\n[2] Cross-device delete (tombstone)")
    B.click("#txn-toggle-5")
    B.wait_for_timeout(200)
    B.click("#txn-list-5 .txn-delete")
    A.wait_for_timeout(1200)
    got = A.text_content("#txn-list-5") or ""
    check("deleted on B vanishes on A", "Zzyzx Trinket" not in got, got[:120])
    ctxA.close(); ctxB.close()

    # ══ 3. offline queue: A offline → add → online → B sees it ══
    print("\n[3] Offline queue")
    reset_fake()
    ctxA, A = new_device(browser)
    ctxB, B = new_device(browser)
    ctxA.set_offline(True)
    add_expense(A, "Offline Widget", 4.25)
    check("offline add shows locally on A", A.input_value("#spent-input-5") == "4.25",
          A.input_value("#spent-input-5"))
    B.wait_for_timeout(800)
    check("B does NOT see it while A offline", "Offline Widget" not in (B.text_content("#txn-list-5") or ""))
    ctxA.set_offline(False)
    A.wait_for_timeout(700)    # A's outbox flushes on next poll tick
    B.wait_for_timeout(1000)
    got = B.text_content("#txn-list-5") or ""
    check("after A reconnects, B sees the expense", "Offline Widget" in got, got[:120])
    ctxA.close(); ctxB.close()

    # ══ 4. LWW conflict on a setting ══
    print("\n[4] Last-write-wins on settings")
    reset_fake()
    ctxA, A = new_device(browser)
    ctxB, B = new_device(browser)
    A.fill("#alloc-rent", "2100"); A.wait_for_timeout(400)
    B.fill("#alloc-rent", "2200"); B.wait_for_timeout(1200)   # B writes later → should win
    A.wait_for_timeout(1200)
    check("later write (B=2200) wins on A", A.input_value("#alloc-rent") == "2200", A.input_value("#alloc-rent"))
    check("B keeps its own value", B.input_value("#alloc-rent") == "2200", B.input_value("#alloc-rent"))
    ctxA.close(); ctxB.close()

    # ══ 5. first-sign-in migration uploads pre-existing local data ══
    print("\n[5] Migration")
    reset_fake()
    ctxA = browser.new_context(viewport={"width": 390, "height": 844})
    p1 = new_page(ctxA, with_backend=False)    # no sync — Phase 1 behavior
    add_expense(p1, "Legacy Gadget", 55.00)
    p1.close()
    p2 = new_page(ctxA, with_backend=True)     # same device signs in for the first time
    p2.wait_for_timeout(900)
    ctxB, B = new_device(browser)              # fresh second device
    B.wait_for_timeout(1200)
    got = B.text_content("#txn-list-5") or ""
    check("fresh device receives migrated data", "Legacy Gadget" in got, got[:120])
    ctxA.close(); ctxB.close()

    browser.close()

httpd.shutdown()
print(f"\n{'='*50}\nRESULT: {len(passed)} passed, {len(failed)} failed")
for name, detail in failed:
    print(f"  FAILED: {name} — {detail}")
sys.exit(1 if failed else 0)
