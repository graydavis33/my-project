# Expense Tracker

## What It Does
- Scans Gmail for personal expense emails from the last 30 days (receipts, subscriptions, bills, bank card alerts)
- Extracts date, vendor, amount, and category using Claude Haiku (batches of 5)
- Auto-categorizes into 7 buckets: Groceries, Dining Out, Software & Tools, Utilities, Investments, BJJ & Kickboxing, Misc (matches the Payday Checklist categories; the Haiku prompt uses these 7 directly as of 2026-07-07)
- Parses bank/money-app alert emails so spend with no receipt email gets captured — verified senders (2026-07-07): PrimeSouth Zelle sends (`alerts.primesouth.com`) + Rocket Money large/uncategorized alerts (`email.rocketmoney.com`); card-swipe alerts pending Gray enabling them in the PrimeSouth app. Senders in `config.ALERT_SENDERS`; the same purchase reported by multiple sources (receipt/PrimeSouth/Rocket, same amount within 2 days) collapses to one via `main.dedupe_bank_alerts`
- Optionally mirrors expenses into Firestore (`firestore_writer.py`, `households/gray/transactions/{email_id}`, create-only so app-side edits/deletes never get overwritten) — active only when `FIREBASE_SERVICE_ACCOUNT` env holds the service-account JSON
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
