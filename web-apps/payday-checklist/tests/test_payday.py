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
    check("tax step defaults to 1950", page.input_value("#alloc-tax") == "1950", page.input_value("#alloc-tax"))
    check("balance chain: after rent $2,650", "2,650" in page.text_content("#balance-1"))
    check("balance chain: after loans $1,650", "1,650" in page.text_content("#balance-2"))
    check("balance chain: after EF $1,250", "1,250" in page.text_content("#balance-3"))
    check("balance chain: budget pool $1,050", "1,050" in page.text_content("#balance-4"))
    check("budget total $850", page.text_content("#expense-budget-total").strip() == "$850")

    # ══ 2. expenses.json retired (2026-07-15) — app must NOT fetch it ══
    # Expenses now arrive only via Firestore sync (Plaid + gmail written server-side).
    print("\n[2] no expenses.json fetch")
    fetched = page.evaluate("""() =>
      performance.getEntriesByType('resource').some(r => r.name.includes('expenses.json'))""")
    check("app never requests expenses.json", not fetched)

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
    check("tax recomputes to 2100", page.input_value("#alloc-tax") == "2100", page.input_value("#alloc-tax"))
    page.fill("#alloc-rent", "2000")
    page.wait_for_timeout(200)
    check("rent change updates chain", "2,900" in page.text_content("#balance-1"),
          page.text_content("#balance-1"))
    # manual tax override: free-form dollar amount wins over the % suggestion
    page.fill("#alloc-tax", "2000")
    page.wait_for_timeout(200)
    check("manual tax edit updates after-tax", "5,000" in page.text_content("#balance-0"),
          page.text_content("#balance-0"))
    page.reload(); wait_ready(page); page.wait_for_timeout(800)
    check("manual tax 2000 persists", page.input_value("#alloc-tax") == "2000", page.input_value("#alloc-tax"))
    page.fill("#tax-percent", "30")   # editing % recomputes from scratch
    page.wait_for_timeout(200)
    check("tax %% edit recomputes amount", page.input_value("#alloc-tax") == "2100", page.input_value("#alloc-tax"))
    page.fill("#alloc-tax", "2000")   # restore the manual value for later sections
    page.wait_for_timeout(200)

    # ══ 5. Misc overflow hint ══
    print("\n[5] Misc buffer overflow hint")
    hint = page.text_content("#misc-overflow")
    check("misc hint shows $140 untouched → $70/$70", "$140" in hint and "$70" in hint, hint)

    # ══ 6. Steps + fund balances ══
    print("\n[6] Steps + funds")
    if "done" not in page.get_attribute("#step-0", "class"):  # may already be auto-checked by a real tax transfer
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

    # synced-source txn delete → tombstone survives reload (no resurrection path)
    page.evaluate("""async () => {
      await addTransaction({
        vendor: 'Sandcastles', amount: 49, category: 'Software & Tools',
        date: new Date().toISOString().slice(0,10), month: new Date().toISOString().slice(0,7),
        note: '', source: 'gmail', email_id: 'e2e-gmail-del', sid: 'e2e-gmail-del',
        createdAt: new Date().toISOString(), updatedAt: Date.now()
      });
    }""")
    page.reload(); wait_ready(page); page.wait_for_timeout(800)
    check("injected synced receipt shows in Software & Tools", spent_value(page, 2) == "49",
          spent_value(page, 2))
    page.click("#txn-toggle-2")
    page.wait_for_timeout(200)
    page.click("#txn-list-2 .txn-delete")
    page.wait_for_timeout(300)
    page.reload(); wait_ready(page); page.wait_for_timeout(1000)
    check("deleted synced receipt stays deleted after reload", spent_value(page, 2) == "",
          spent_value(page, 2))

    # ══ 10. History save + render ══
    print("\n[10] History")
    page.click(".btn-row .gm-btn-primary")  # Save Month to History
    page.wait_for_timeout(300)
    page.click(".gm-tabs .gm-tab-btn:nth-child(4)")  # History (tabs: Checklist/Write-Offs/Reimburse/History)
    page.wait_for_timeout(300)
    hist = page.text_content("#history-list")
    check("history entry rendered", "Total spent" in hist and "$7,000 month" in hist, hist[:150])
    page.click(".gm-tabs .gm-tab-btn:nth-child(1)")

    # ══ 10.5 Business write-offs ══
    print("\n[10.5] Business write-offs")
    page.click(".fab")
    page.fill("#add-vendor", "B&H Photo")
    page.fill("#add-amount", "199.99")
    page.select_option("#add-category", "Misc")
    page.click(".add-modal .gm-btn-primary")
    page.wait_for_timeout(300)
    before = page.evaluate("() => autoSpentFor(MISC_INDEX)")
    page.evaluate("() => { const t = TXN_CACHE.find(x => x.vendor === 'B&H Photo'); return setWriteOff(t.id, true); }")
    page.wait_for_timeout(300)
    after = page.evaluate("() => autoSpentFor(MISC_INDEX)")
    check("write-off leaves personal budget", abs(before - after - 199.99) < 0.01, f"{before} -> {after}")
    check("vendor rule learned", page.evaluate("() => BUSINESS_VENDORS.includes('b&h photo')"))
    # future purchase from the same vendor auto-marks
    page.click(".fab")
    page.fill("#add-vendor", "B&H Photo")
    page.fill("#add-amount", "50")
    page.select_option("#add-category", "Misc")
    page.click(".add-modal .gm-btn-primary")
    page.wait_for_timeout(300)
    auto = page.evaluate("() => autoSpentFor(MISC_INDEX)")
    check("future vendor purchase auto-marked", abs(auto - after) < 0.01, f"{after} -> {auto}")
    page.click(".gm-tabs .gm-tab-btn:nth-child(2)")  # Write-Offs tab
    page.wait_for_timeout(300)
    biz = page.text_content("#biz-txn-list") or ""
    check("business tab lists both write-offs", biz.count("B&H Photo") == 2, biz[:150])
    total = page.text_content("#biz-month-total") or ""
    check("business month total = $249.99", "249.99" in total, total)
    # unmark one: explicit false beats the vendor rule
    page.evaluate("() => { const t = TXN_CACHE.find(x => x.vendor === 'B&H Photo' && x.amount === 50); return unmarkBusiness(t.id); }")
    page.wait_for_timeout(300)
    check("unmarked txn back in personal budget", abs(page.evaluate("() => autoSpentFor(MISC_INDEX)") - auto - 50) < 0.01)
    # removing the vendor rule releases the rest
    page.evaluate("() => removeBusinessVendor('b&h photo')")
    page.wait_for_timeout(300)
    check("rule removed -> explicit write-off stays", page.evaluate("() => TXN_CACHE.filter(t => isBusiness(t)).length") == 1)
    # ── reimbursements ──
    page.click(".fab")
    page.fill("#add-vendor", "Home Depot")
    page.fill("#add-amount", "30")
    page.select_option("#add-category", "Misc")
    page.click(".add-modal .gm-btn-primary")
    page.wait_for_timeout(300)
    before_r = page.evaluate("() => autoSpentFor(MISC_INDEX)")
    page.evaluate("() => { const t = TXN_CACHE.find(x => x.vendor === 'Home Depot'); return setReimb(t.id, false); }")
    page.wait_for_timeout(300)
    check("one-time reimb leaves personal budget", abs(page.evaluate("() => autoSpentFor(MISC_INDEX)") - before_r + 30) < 0.01)
    check("one-time reimb creates NO vendor rule", page.evaluate("() => REIMBURSE_VENDORS.length") == 0)
    owed = page.text_content("#reimb-owed") or ""
    check("awaiting total shows $30", "30.00" in owed, owed)
    # recurring reimb vendor
    page.evaluate("() => { const t = TXN_CACHE.find(x => x.vendor === 'Home Depot'); return setReimb(t.id, true); }")
    page.wait_for_timeout(200)
    check("recurring reimb learns vendor", page.evaluate("() => REIMBURSE_VENDORS.includes('home depot')"))
    page.click(".fab")
    page.fill("#add-vendor", "Home Depot")
    page.fill("#add-amount", "12")
    page.select_option("#add-category", "Misc")
    page.click(".add-modal .gm-btn-primary")
    page.wait_for_timeout(300)
    check("future vendor purchase auto-opens", page.evaluate("() => TXN_CACHE.filter(t => reimbStatus(t) === 'open').length") == 2)
    # repaid drops from awaiting but tracks YTD
    page.evaluate("() => { const t = TXN_CACHE.find(x => x.vendor === 'Home Depot' && x.amount === 30); return markRepaid(t.id); }")
    page.wait_for_timeout(300)
    check("repaid leaves awaiting list", page.evaluate("() => TXN_CACHE.filter(t => reimbStatus(t) === 'open').length") == 1)
    check("repaid stays out of personal budget", abs(page.evaluate("() => autoSpentFor(MISC_INDEX)") - before_r + 30) < 0.01)
    # unmark with rule active pins 'none' (stays personal despite the rule)
    page.evaluate("() => { const t = TXN_CACHE.find(x => x.vendor === 'Home Depot' && x.amount === 12); return unmarkReimbursable(t.id); }")
    page.wait_for_timeout(300)
    check("unmark beats the vendor rule", page.evaluate("() => TXN_CACHE.filter(t => reimbStatus(t) === 'open').length") == 0)
    page.evaluate("() => removeReimburseVendor('home depot')")
    page.wait_for_timeout(200)
    page.click(".gm-tabs .gm-tab-btn:nth-child(1)")
    page.wait_for_timeout(300)
    # clean up the test txns so later sections' math is unaffected
    page.evaluate("() => Promise.all(TXN_CACHE.filter(t => ['B&H Photo','Home Depot'].includes(t.vendor)).map(t => { t.deleted = true; t.updatedAt = Date.now(); if (!t.sid) t.sid = uuidSid(); return addTransaction(t); }))")
    page.evaluate("() => { TXN_CACHE = TXN_CACHE.filter(t => !['B&H Photo','Home Depot'].includes(t.vendor)); refreshExpenseDisplays(); }")
    page.wait_for_timeout(200)

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

    # ══ 13. Edward Jones transfers → EJ card + tax step auto-check ══
    print("\n[13] Edward Jones card")
    import time as _time
    month = _time.strftime("%Y-%m")
    # reset steps so we can observe the auto-check transition
    page.click(".gm-label .section-reset-btn")   # first reset btn = steps
    page.wait_for_timeout(300)
    check("step 0 unchecked after reset", "done" not in page.get_attribute("#step-0", "class"))
    page.evaluate("""async (month) => {
      const mk = (kind, vendor, amount, eid) => ({
        vendor, amount, kind,
        category: kind === 'tax_transfer' ? 'Tax Set-Aside' : 'EJ Investing',
        date: month + '-07', month, note: '', source: 'gmail',
        email_id: eid, sid: eid,
        createdAt: new Date().toISOString(), updatedAt: Date.now()
      });
      await addTransaction(mk('tax_transfer', 'Edward Jones (Sole Proprietor-1)', 3000, 'ejtest-tax'));
      await addTransaction(mk('invest_transfer', 'Edward Jones (Single-1)', 100, 'ejtest-inv'));
    }""", month)
    page.reload(); wait_ready(page); page.wait_for_timeout(1000)
    # Totals = whatever's in TXN_CACHE (Firestore sync may carry real transfers too),
    # so compute expected from app state rather than hardcoding.
    exp_tax = page.evaluate("() => TXN_CACHE.filter(t => (t.kind==='tax_transfer'||t.category==='Tax Set-Aside') && (t.date||'').startsWith(String(new Date().getFullYear()))).reduce((s,t)=>s+t.amount,0)")
    exp_inv = page.evaluate("() => TXN_CACHE.filter(t => (t.kind==='invest_transfer'||t.category==='EJ Investing') && (t.date||'').startsWith(String(new Date().getFullYear()))).reduce((s,t)=>s+t.amount,0)")
    check("EJ tax total includes injected $3,000", exp_tax >= 3000,
          f"cache tax total {exp_tax}")
    check("EJ tax card matches cache", page.text_content("#ej-tax-total").strip() == "$" + f"{exp_tax:,.0f}",
          page.text_content("#ej-tax-total"))
    check("EJ invest total includes injected $100", exp_inv >= 100,
          f"cache invest total {exp_inv}")
    check("EJ invest card matches cache", page.text_content("#ej-invest-total").strip() == "$" + f"{exp_inv:,.0f}",
          page.text_content("#ej-invest-total"))
    check("tax step auto-checked by sole-prop transfer", "done" in page.get_attribute("#step-0", "class"))
    note = page.text_content("#ej-note") or ""
    check("EJ note shows sent amount", "3,000" in note, note)
    # transfers must NOT touch budget rows (kind-tagged records skip every category incl. Misc)
    check("transfers don't pollute budgets", page.evaluate("() => CATEGORIES.every((_, i) => autoSpentFor(i) < 3000)"), str(page.evaluate("() => CATEGORIES.map((_, i) => autoSpentFor(i))")))

    # ══ 14. Screenshots ══
    print("\n[14] Screenshots")
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
