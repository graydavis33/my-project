"""End-to-end tests for the rebuilt Payday Checklist PWA."""
import sys, os

sys.stdout.reconfigure(encoding="utf-8")   # Windows cp1252 console can't print → / ✓

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import start_server, WEBAPPS_DIR

PORT = 4781
URL = f"http://localhost:{PORT}/payday-checklist/index.html"
SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".artifacts")
os.makedirs(SCRATCH, exist_ok=True)

passed, failed = [], []

def check(name, cond, detail=""):
    if cond:
        passed.append(name)
        print(f"  PASS  {name}")
    else:
        failed.append((name, detail))
        print(f"  FAIL  {name}  {detail}")

httpd = start_server(PORT)
print(f"Serving {WEBAPPS_DIR} on :{PORT}")

from playwright.sync_api import sync_playwright

def wait_ready(page):
    page.wait_for_selector("body[data-ready='1']", timeout=10000)

def spent_value(page, i):
    return page.input_value(f"#spent-input-{i}")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    console_errors = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())

    # ══ 1. Initial load ══
    print("\n[1] Initial load")
    page.goto(URL)
    wait_ready(page)
    page.wait_for_timeout(800)  # let gmail sync finish
    check("no console errors on load", not console_errors, str(console_errors[:3]))
    check("monthly income shows $6,500", page.text_content("#context-paycheck").strip() == "$6,500",
          page.text_content("#context-paycheck"))
    check("after-tax shows $4,550", "4,550" in page.text_content("#context-aftertax"))
    check("tax step shows -$1,950", "1,950" in page.text_content("#step-0-amount"))
    check("balance chain: after rent $2,650", "2,650" in page.text_content("#balance-1"))
    check("balance chain: after loans $1,650", "1,650" in page.text_content("#balance-2"))
    check("balance chain: after EF $1,250", "1,250" in page.text_content("#balance-3"))
    check("balance chain: budget pool $1,050", "1,050" in page.text_content("#balance-4"))
    check("budget total $950", page.text_content("#expense-budget-total").strip() == "$950")

    # ══ 2. Gmail expenses.json merge (Sandcastles $49 → Software & Tools, July 2026) ══
    print("\n[2] Gmail sync merge")
    sw_spent = spent_value(page, 2)
    check("Sandcastles $49 imported into Software & Tools", sw_spent == "49", f"got '{sw_spent}'")
    sync_txt = page.text_content("#sync-status")
    check("sync badge shows 1 receipt", "1 receipt" in sync_txt, sync_txt)

    # reload → dedup (must stay 49, not double to 98)
    page.reload(); wait_ready(page); page.wait_for_timeout(800)
    sw_spent = spent_value(page, 2)
    check("no double-import after reload (still 49)", sw_spent == "49", f"got '{sw_spent}'")

    # ══ 3. Manual expense + auto-categorization ══
    print("\n[3] Manual entry + auto-categorize")
    page.click(".fab")
    page.fill("#add-vendor", "Trader Joe's")
    page.wait_for_timeout(200)
    suggest = page.text_content("#add-suggest")
    check("suggests Groceries for Trader Joe's", "Groceries" in (suggest or ""), str(suggest))
    page.fill("#add-amount", "43.27")
    page.click("#add-suggest button")  # accept suggestion
    check("suggestion click sets category", page.input_value("#add-category") == "Groceries")
    page.click(".add-modal .gm-btn-primary")
    page.wait_for_timeout(300)
    check("groceries spent = 43.27", spent_value(page, 0) == "43.27", spent_value(page, 0))
    rem = page.text_content("#rem-display-0")
    check("groceries remaining = $157", rem.strip() == "$157", rem)

    # learned categorization: add same vendor again, should suggest from history
    page.click(".fab")
    page.fill("#add-vendor", "trader joe's")   # lowercase — tests learned match
    page.wait_for_timeout(200)
    suggest = page.text_content("#add-suggest")
    check("learned suggestion for repeat vendor", "Groceries" in (suggest or ""), str(suggest))
    page.click(".modal-close")

    # BJJ keyword
    page.click(".fab")
    page.fill("#add-vendor", "Renzo Gracie Academy")
    page.wait_for_timeout(200)
    suggest = page.text_content("#add-suggest") or ""
    check("suggests BJJ & Kickboxing for Renzo Gracie", "BJJ" in suggest, suggest)
    page.click(".modal-close")

    # ══ 4. Editable income + allocations recompute ══
    print("\n[4] Editable income/allocations")
    page.fill("#paycheck-amount", "3500")
    page.wait_for_timeout(200)
    check("monthly updates to $7,000", page.text_content("#context-paycheck").strip() == "$7,000")
    check("tax updates to -$2,100", "2,100" in page.text_content("#step-0-amount"))
    page.fill("#alloc-rent", "2000")
    page.wait_for_timeout(200)
    check("rent change updates chain", "2,900" in page.text_content("#balance-1"),
          page.text_content("#balance-1"))

    # ══ 5. Misc overflow hint ══
    print("\n[5] Misc buffer overflow hint")
    hint = page.text_content("#misc-overflow")
    check("misc hint shows $140 untouched → $70/$70", "$140" in hint and "$70" in hint, hint)

    # ══ 6. Steps + fund balances ══
    print("\n[6] Steps + funds")
    page.click("#step-0")
    check("step 0 marked done", "done" in page.get_attribute("#step-0", "class"))
    page.fill("#fund-balance", "3000")
    page.wait_for_timeout(200)
    check("fund 25% there", "25%" in page.text_content("#fund-pct"))
    check("fund months uses editable EF amount", "23 month" in page.text_content("#fund-months"),
          page.text_content("#fund-months"))  # (12000-3000)/400 = 22.5 → 23

    # ══ 7. Persistence across reload ══
    print("\n[7] Persistence across reload")
    page.reload(); wait_ready(page); page.wait_for_timeout(800)
    check("paycheck 3500 persisted", page.input_value("#paycheck-amount") == "3500")
    check("rent 2000 persisted", page.input_value("#alloc-rent") == "2000")
    check("groceries 43.27 persisted", spent_value(page, 0) == "43.27", spent_value(page, 0))
    check("step 0 still done", "done" in page.get_attribute("#step-0", "class"))
    check("fund balance 3000 persisted", page.input_value("#fund-balance") == "3000")

    # ══ 8. Manual override of spent input ══
    print("\n[8] Manual spent override")
    page.fill("#spent-input-1", "75")
    page.wait_for_timeout(300)
    page.reload(); wait_ready(page); page.wait_for_timeout(800)
    check("dining override 75 persisted", spent_value(page, 1) == "75", spent_value(page, 1))
    page.fill("#spent-input-1", "")
    page.wait_for_timeout(300)
    page.reload(); wait_ready(page); page.wait_for_timeout(800)
    check("cleared override returns to auto (empty)", spent_value(page, 1) == "", spent_value(page, 1))

    # ══ 9. Transaction list + delete ══
    print("\n[9] Transaction list + delete")
    toggle_txt = page.text_content("#txn-toggle-0")
    check("groceries shows 1 transaction", "1 transaction" in toggle_txt, toggle_txt)
    page.click("#txn-toggle-0")
    page.wait_for_timeout(300)
    check("txn list shows Trader Joe's", "Trader Joe" in page.text_content("#txn-list-0"))
    page.click("#txn-list-0 .txn-delete")   # dialog auto-accepted
    page.wait_for_timeout(300)
    check("after delete groceries empty", spent_value(page, 0) == "", spent_value(page, 0))

    # gmail txn delete → dismissed (no re-import on reload)
    page.click("#txn-toggle-2")
    page.wait_for_timeout(200)
    page.click("#txn-list-2 .txn-delete")
    page.wait_for_timeout(300)
    page.reload(); wait_ready(page); page.wait_for_timeout(1000)
    check("deleted gmail receipt stays dismissed after reload", spent_value(page, 2) == "",
          spent_value(page, 2))

    # ══ 10. History save + render ══
    print("\n[10] History")
    page.click(".btn-row .gm-btn-primary")  # Save Month to History
    page.wait_for_timeout(300)
    page.click(".gm-tabs .gm-tab-btn:nth-child(2)")
    page.wait_for_timeout(300)
    hist = page.text_content("#history-list")
    check("history entry rendered", "Total spent" in hist and "$7,000 month" in hist, hist[:150])
    page.click(".gm-tabs .gm-tab-btn:nth-child(1)")

    # ══ 11. CSV export → wipe → import round-trip ══
    print("\n[11] CSV backup round-trip")
    # re-add a transaction so there's data to back up
    page.click(".fab")
    page.fill("#add-vendor", "Whole Foods")
    page.fill("#add-amount", "62.10")
    page.click(".add-modal .gm-btn-primary")
    page.wait_for_timeout(300)
    with page.expect_download() as dl:
        page.click("text=Export Backup")
    csv_path = os.path.join(SCRATCH, "payday-backup-test.csv")
    dl.value.save_as(csv_path)
    check("CSV downloaded", os.path.exists(csv_path) and os.path.getsize(csv_path) > 100)

    # wipe everything (dialogs auto-accepted; page reloads itself)
    page.click("text=Reset Everything")
    page.wait_for_timeout(1500)
    wait_ready(page); page.wait_for_timeout(800)
    check("after reset paycheck back to default", page.input_value("#paycheck-amount") == "3250")
    # NOTE: gmail receipt re-imports after reset (dismissed list wiped) — expected; clear it again
    # import the backup
    with page.expect_file_chooser() as fc:
        page.click("text=Import Backup")
    fc.value.set_files(csv_path)
    page.wait_for_timeout(2000)   # import + auto-reload
    wait_ready(page); page.wait_for_timeout(800)
    check("import restored paycheck 3500", page.input_value("#paycheck-amount") == "3500",
          page.input_value("#paycheck-amount"))
    check("import restored Whole Foods 62.1", spent_value(page, 0) == "62.1", spent_value(page, 0))
    check("import restored fund 3000", page.input_value("#fund-balance") == "3000")

    # ══ 12. Offline mode (service worker) ══
    print("\n[12] Offline (service worker)")
    page.wait_for_timeout(1500)   # give SW time to install + cache
    ctx.set_offline(True)
    page.reload();
    try:
        wait_ready(page)
        page.wait_for_timeout(500)
        check("app loads offline via service worker", True)
        check("offline: data still present", page.input_value("#paycheck-amount") == "3500")
        sync_txt = page.text_content("#sync-status") or ""
        # offline fetch of expenses.json → cached copy OR graceful failure message; both fine
        check("offline: sync badge doesn't crash", sync_txt != "", sync_txt)
        # manual entry works offline
        page.click(".fab")
        page.fill("#add-vendor", "Offline Deli")
        page.fill("#add-amount", "15")
        page.click(".add-modal .gm-btn-primary")
        page.wait_for_timeout(300)
        check("offline: manual entry works", "15" in (spent_value(page, 1) or ""), spent_value(page, 1))
    except Exception as e:
        check("app loads offline via service worker", False, str(e)[:120])
    ctx.set_offline(False)

    # ══ 13. Screenshots ══
    print("\n[13] Screenshots")
    page.reload(); wait_ready(page); page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SCRATCH, "payday-mobile.png"), full_page=True)
    desktop = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    desktop.goto(URL)
    desktop.wait_for_selector("body[data-ready='1']", timeout=10000)
    desktop.wait_for_timeout(1000)
    desktop.screenshot(path=os.path.join(SCRATCH, "payday-desktop.png"))
    # modal screenshot
    page.click(".fab")
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SCRATCH, "payday-modal.png"))
    print("  saved payday-mobile.png / payday-desktop.png / payday-modal.png")

    if console_errors:
        print("\nConsole errors seen:", console_errors[:5])
    browser.close()

httpd.shutdown()
print(f"\n{'='*50}\nRESULT: {len(passed)} passed, {len(failed)} failed")
for name, detail in failed:
    print(f"  FAILED: {name} — {detail}")
sys.exit(1 if failed else 0)
