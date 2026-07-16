# Expense Tracker

## What It Does
- Scans Gmail for personal expense emails from the last 30 days (receipts, subscriptions, bills, bank card alerts)
- Extracts date, vendor, amount, and category using Claude Haiku (batches of 5)
- Auto-categorizes into 7 buckets: Groceries, Dining Out, Software & Tools, Utilities, Investments, BJJ & Kickboxing, Misc (matches the Payday Checklist categories; the Haiku prompt uses these 7 directly as of 2026-07-07)
- Parses bank/money-app alert emails so spend with no receipt email gets captured — verified senders (2026-07-07): PrimeSouth Zelle sends (`alerts.primesouth.com`) + Rocket Money large/uncategorized alerts (`email.rocketmoney.com`); card-swipe alerts pending Gray enabling them in the PrimeSouth app. Senders in `config.ALERT_SENDERS`; the same purchase reported by multiple sources (receipt/PrimeSouth/Rocket, same amount within 2 days) collapses to one via `main.dedupe_bank_alerts`
- Optionally mirrors expenses into Firestore (`firestore_writer.py`, `households/gray/transactions/{email_id}`, create-only so app-side edits/deletes never get overwritten) — active only when `FIREBASE_SERVICE_ACCOUNT` env holds the service-account JSON
- Skips expenses Gray already entered by hand in the app (`main.dedupe_vs_manual`, added 2026-07-08): when Firestore is configured, this month's non-gmail transactions are fetched (`firestore_writer.fetch_non_gmail_transactions`) and any scanned email expense matching one (same amount, dates within 2 days) is dropped before writing — covers the tap-now/alert-posts-later case where Gray types a purchase in before the bank email arrives. Manual tombstones suppress too (a deleted manual entry means "don't count this purchase"). Local runs without Firestore keep everything.
- Edward Jones transfer confirmations parse deterministically (`ej_transfers.py`, no Claude call): Sole Proprietor-* account = Gray's tax set-aside, Single-* = investing. They're allocations, NOT budget expenses — written to the `transfers` array in expenses.json (year-to-date; a dedicated 365-day Gmail fetch backfills the year) and to Firestore with a `kind` field. The app shows them in the "Edward Jones — This Year" card and auto-checks the monthly tax step. The Haiku prompt nulls any bank/Rocket alert describing the same transfer so it can't double-report.
- Filters to current month only, then writes `expenses.json` into the Payday Checklist web app
- Caches scanned email IDs in `.scanned_ids.json` so reruns skip emails already processed

## Key Files
- `main.py` — orchestrates the run: Gmail fetch, Claude extract, write `expenses.json`
- `gmail_client.py` — Gmail OAuth + expense email search query
- `expense_scanner.py` — Claude Haiku extraction, batch logic, dedup cache
- `config.py` — env loading, paths, category list
- `.scanned_ids.json` — tracks already-processed email IDs (auto-created)
- `.expense_cache.json` — caches extracted expenses by email ID (auto-created)

## Stack
Python, Claude (claude-haiku-4-5-20251001), Gmail API, google-auth, python-dotenv

## Run
```bash
cd python-scripts/expense-tracker && python main.py            # full run
cd python-scripts/expense-tracker && python main.py --dry-run  # scan + print, write nothing
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`

Also needs `credentials.json` + `token.json` for Gmail OAuth (readonly scope).

## Status
LIVE — auto-syncs via GitHub Actions. Output lands at `web-apps/payday-checklist/expenses.json`, which the Payday Checklist web app reads to show remaining budget per category.

## Notes
- Only Gmail readonly scope — tool never modifies or sends email
- Batch size 5 per Claude call to keep API costs minimal; falls back to single-email extraction if batch JSON parse fails
- Email body truncated to 1500 chars (batch) / 2000 chars (single) before sending to Claude
- Gmail search query is sender + subject based (DoorDash, Netflix, Spotify, Amazon, Con Edison, etc.) — add new senders to `gmail_client.py` if receipts get missed
- Writes to `../../web-apps/payday-checklist/expenses.json` — path is relative, don't move the project folder
