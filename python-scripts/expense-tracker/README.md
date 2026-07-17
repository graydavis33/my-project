# Expense Tracker

## What It Does
- **Plaid bank feed (primary, added 2026-07-15):** pulls every PrimeSouth transaction via Plaid `/transactions/sync` (read-only, cursor-based incremental) — `plaid_client.py` (network) + `plaid_sync.py` (transform/orchestration) + `category_map.py` (deterministic Plaid-category → app-category map, no AI). Purchases only: income, transfers, rent, and loan payments are excluded by category; pending transactions land same-day and reconcile to posted via `removed`-id tombstones. Writes straight to Firestore, never to a repo file.
- Scans Gmail for personal expense emails from the last 30 days (receipts, subscriptions, bills, bank card alerts) — **kept as a deduped backstop** behind Plaid
- Extracts date, vendor, amount, and category using Claude Haiku (batches of 5)
- Auto-categorizes into 6 buckets: Groceries, Dining Out, Software & Tools, Utilities, BJJ & Kickboxing, Misc (matches the Payday Checklist categories; Investments removed 2026-07-17 — brokerage transactions are skipped, EJ transfers have their own parser)
- Parses bank/money-app alert emails so spend with no receipt email gets captured — verified senders (2026-07-07): PrimeSouth Zelle sends (`alerts.primesouth.com`) + Rocket Money large/uncategorized alerts (`email.rocketmoney.com`). Senders in `config.ALERT_SENDERS`; the same purchase reported by multiple sources (receipt/PrimeSouth/Rocket, same amount within 2 days) collapses to one via `main.dedupe_bank_alerts`
- Writes expenses into Firestore (`firestore_writer.py`, `households/gray/transactions/{id}`, create-only so app-side edits/deletes never get overwritten; the one deliberate exception is `tombstone_removed` marking dropped Plaid pendings deleted) — active only when `FIREBASE_SERVICE_ACCOUNT` env holds the service-account JSON
- Cross-source dedup (`main.dedupe_vs_manual`): gmail expenses dedup against this month's non-gmail Firestore records (`fetch_non_gmail_transactions` — manual entries AND Plaid rows); Plaid expenses dedup against non-Plaid records (`fetch_non_plaid_transactions` — manual AND gmail, because receipt emails land hours before Plaid surfaces the transaction). Match = same amount, dates within 2 days; tombstones suppress too. Plaid keeps a current+previous-month window so month-boundary purchases survive feed lag, and applies `EXCLUDED_VENDORS` so Zelle rent never enters the budget. Local runs without Firestore keep everything.
- Edward Jones transfer confirmations parse deterministically (`ej_transfers.py`, no Claude call): Sole Proprietor-* account = Gray's tax set-aside, Single-* = investing. They're allocations, NOT budget expenses — written to Firestore with a `kind` field (year-to-date; a dedicated 365-day Gmail fetch backfills the year). The app shows them in the "Edward Jones — This Year" card and auto-checks the monthly tax step. Plaid can't split tax vs invest, which is why this email parser stays. The Haiku prompt nulls any bank/Rocket alert describing the same transfer so it can't double-report.
- Filters to current month only. **No `expenses.json` is written (retired 2026-07-15)** — all financial data lives in private Firestore only; the signed-in app receives it live.
- **Quiet mode in CI:** when `GITHUB_ACTIONS=true`, stdout carries counts only — never vendors, amounts, or category totals (public repo = public Action logs)
- Caches scanned email IDs in `.scanned_ids.json` so reruns skip emails already processed

## Key Files
- `main.py` — orchestrates the run: Plaid sync, Gmail fetch, Claude extract, Firestore write
- `plaid_client.py` — thin read-only Plaid API wrapper (link token, token exchange, /transactions/sync)
- `plaid_sync.py` — Plaid transaction → expense transform + the sync step (filter, categorize, dedup, write)
- `category_map.py` — deterministic Plaid `personal_finance_category` → 7-category map + vendor overrides
- `connect_bank.py` — one-time local Plaid Link flow; pushes the access token to the `PLAID_ACCESS_TOKEN` GitHub secret (never printed/committed)
- `firestore_writer.py` — create-only Firestore writes, dedup fetchers, Plaid sync cursor, tombstones
- `gmail_client.py` — Gmail OAuth + expense email search query
- `expense_scanner.py` — Claude Haiku extraction, batch logic, dedup cache
- `config.py` — env loading, paths, category list
- `.scanned_ids.json` — tracks already-processed email IDs (auto-created)
- `.expense_cache.json` — caches extracted expenses by email ID (auto-created)

## Stack
Python, Plaid (plaid-python, Transactions read-only), Claude (claude-haiku-4-5-20251001), Gmail API, google-auth, firebase-admin, python-dotenv

## Run
```bash
cd python-scripts/expense-tracker && python main.py            # full run
cd python-scripts/expense-tracker && python main.py --dry-run  # scan + print, write nothing
cd python-scripts/expense-tracker && python connect_bank.py    # one-time: connect the bank via Plaid Link
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV` (sandbox|production, default production), `PLAID_ACCESS_TOKEN` (local runs; in CI it's an Actions secret), `FIREBASE_SERVICE_ACCOUNT` (service-account JSON, optional locally)

Also needs `credentials.json` + `token.json` for Gmail OAuth (readonly scope).

## Status
LIVE — auto-syncs via GitHub Actions every ~30 min. All output lands in private Firestore (`households/gray`); the Payday Checklist app reads it live when signed in.

## Notes
- Plaid access is READ-ONLY (Transactions product only) — the token cannot move money
- Only Gmail readonly scope — tool never modifies or sends email
- Batch size 5 per Claude call to keep API costs minimal; falls back to single-email extraction if batch JSON parse fails
- Email body truncated to 1500 chars (batch) / 2000 chars (single) before sending to Claude
- Gmail search query is sender + subject based (DoorDash, Netflix, Spotify, Amazon, Con Edison, etc.) — add new senders to `gmail_client.py` if receipts get missed
- A Plaid failure (outage, expired token) is caught and logged; the Gmail backstop still runs in that same execution
