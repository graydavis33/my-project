# Payday Checklist — Phase 1 Spec

**Version:** 2026-07-06  
**Status:** ✅ BUILT + TESTED (46/46 Playwright end-to-end tests green, incl. offline + backup round-trip)

> **Phase 2 (2026-07-07): cross-device Firebase sync + full expense automation is BUILT** — see
> `docs/superpowers/specs/2026-07-07-payday-sync-and-expense-automation-design.md` (design) and
> `PHASE2-HANDOFF.md` (Gray's remaining console steps). The e2e suites now live in `tests/`.

**Implementation notes (what shipped vs this spec):**
- Auto-categorization is LOCAL (keyword rules + learns from your past vendors), NOT Haiku — a client-side API call on a public GitHub Pages site would expose the API key. The Gmail scanner still uses Haiku server-side in the daily Action.
- Gmail receipts merge into the same transaction store (dedup by email_id; deleting one keeps it dismissed).
- Old-category receipts (Streaming/Transport/Health & Wellness/Shopping) map to Misc.
- Student loans moved from a budget row to checklist step 3 (-$1,000/mo, editable) per the 20%-interest priority call.
- Test suite: scratchpad `test_payday.py` (rerunnable; serves web-apps/ locally + drives Chromium).

---

## Monthly Income & Allocations

**Monthly Paycheck:** $6,500 (2 × $3,250 bi-weekly)

**Taxes:** 30% (editable %) — default $1,950/month  
**After-tax income:** ~$4,550

**Fixed monthly allocations (editable $):**
- Rent: $1,900
- Emergency Fund transfer: $400
- Student Loans payment: $1,000
- Ring Fund transfer: $200

**Remaining for budgets:** $1,050

---

## Monthly Expense Budgets (all editable)

1. Groceries — $200
2. Dining Out — $150
3. Software & Tools — $100
4. Utilities — $60 (WiFi + electricity)
5. Investments — $100
6. BJJ & Kickboxing — $200
7. **Misc buffer — $140** (try not to spend; overflow 50/50 → ring + loans)

**Total budgets:** $950

---

## Misc Buffer Strategy

- Allocate $140/month as a silo (try not to touch)
- If month-end balance > $0: split 50/50 between Ring Fund and Student Loans
- Example: spend $10 from $140 → $130 left → $65 ring + $65 loans
- Refill to $140 next month, repeat

---

## Emergency Fund & Ring Fund Goals

- **Emergency Fund goal:** $12,000 (editable) — $400/month target
- **Ring Fund goal:** $10,000 (editable) — $200/month target + misc overflow

---

## Phase 1 Features

### Data Layer
- **Storage:** IndexedDB (local database, survives offline, persistent)
- **Schema:**
  - `transactions` table: date, vendor, amount, category, notes
  - `settings` table: paycheck %, rent, all budgets, fund goals, fund balances, notes, steps completed

### UI Changes
- **Top:** Show "Monthly Paycheck: $6,500" context clearly
- **Editable inputs:**
  - Paycheck amount (default $3,250)
  - Tax % (default 30%)
  - Rent amount (default $1,900)
  - All budget amounts
  - Fund goals
  - Fund balances
- **Manual entry:**
  - "+ Add Expense" button (floating action or prominent placement)
  - Modal: vendor name, amount, category dropdown, date, optional notes
  - Auto-categorize suggestion (Haiku): "Starbucks" → suggests "Dining Out"
  - Submit → stores to IndexedDB, displays in expense list immediately
- **Backup/Restore:**
  - Export button → downloads all history + settings as CSV
  - Import button → restores from CSV (confirms before overwriting)

### Offline Support
- Service worker caches HTML/CSS/JS
- App shell loads instantly, no Wi-Fi needed
- Manual entry works offline, stores locally
- When online: data persists (Phase 2: sync to Firebase)

### PWA Setup
- `manifest.json`: app name, icon, colors, install prompt
- Service worker: offline caching + install event
- iOS meta tags: app-capable, splash screen, status bar
- GitHub Pages auto-deploys

### History & Export
- History tab shows past paychecks (editable + deletable)
- CSV export includes all transactions + settings snapshots
- CSV import restores exact state

---

## Build Order

1. Write spec file ✅
2. Refactor HTML (add "+ Add Expense", backup buttons, clear paycheck context)
3. IndexedDB schema + data migration from localStorage
4. Manual entry modal + Haiku auto-categorize
5. CSV export/import
6. Service worker + PWA manifest
7. Test on phone (PWA install, manual entry, offline)
8. Deploy to GitHub Pages

---

## Success Criteria

- [ ] App installs as PWA on iPhone (home screen icon)
- [ ] Manual "+ Add Expense" works, auto-categorizes
- [ ] Offline: manual entry + reads work without Wi-Fi
- [ ] All data persists (IndexedDB)
- [ ] CSV backup/restore works
- [ ] Monthly paycheck context is clear ($6,500)
- [ ] All budgets/amounts are editable inline
- [ ] Ready to use by July 9

