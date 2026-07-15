# Payday Checklist — Plaid Bank Sync (Design)

_Date: 2026-07-15 · Status: approved design, pre-plan_

> Privacy note: this spec is committed to a PUBLIC repo. It contains NO balances,
> amounts, or account numbers by design — structure and category names only.

---

## Problem

The Payday Checklist's expense pipeline parses **bank-alert emails** to capture
purchases. That approach structurally misses transactions: the bank decides which
purchases trigger an email, and PrimeSouth does not email all of them (root cause
of the 2026-07 "banana purchase" miss — the bank sent no email at all). Gray wants
**every** purchase captured automatically.

Two existing privacy leaks compound the problem and must be closed in the same work:

1. **`web-apps/payday-checklist/expenses.json` is committed** to the public repo,
   with **193 historical versions** in git history — each holding real vendor names,
   amounts, people's names, and Edward Jones transfer figures.
2. **GitHub Actions run logs are public** on a public repo, and the scanner prints
   vendor + amount + category totals to stdout on every ~30-minute run.

The repo cannot be made private (Free plan — going private disables GitHub Pages,
which hosts the PWA and the TikTok OAuth callback). So the requirement is: keep all
financial data entirely off every public surface (repo, git history, Actions logs).

## Goals

- Capture ~100% of PrimeSouth purchases automatically via a real bank-data feed.
- **Zero financial data on any public surface** — repo, git history, or CI logs.
- Reuse the existing infrastructure (the `expense-tracker` tool, its GitHub Actions
  workflow, and the Firestore backend) rather than building a new tool.
- Read-only access to the bank. No ability to move money.
- Stay within Plaid's free tier.

## Non-goals

- Multi-bank / credit-card ingestion. All spending is on the one PrimeSouth account
  (confirmed with Gray). Plaid's free Trial plan supports up to 10 connected accounts
  if that ever changes; only 1 is needed now.
- Any write/payment capability. Transactions product only (read-only).
- A paid Plaid plan. The free Trial plan (up to 10 connected accounts, no time limit,
  real production data, Transactions included) covers this use indefinitely at 1 account.
- Replacing the Firebase cross-device sync (already live and used as the app's source
  of truth when signed in).

## Locked decisions

| Decision | Choice |
|---|---|
| Architecture | **Approach A** — extend the existing `expense-tracker` tool + its workflow |
| Aggregator | **Plaid** (Transactions, read-only, Production env on the free Trial plan) |
| Primary vs. backstop | Plaid is **primary**; Gmail receipt scanning **stays as a deduped backstop** |
| Edward Jones | Keep the existing EJ **email** parser — Plaid can't split "taxes" vs "investing" |
| Data location | **Firestore only** for all financial data; retire `expenses.json` entirely |
| Git history | **Scrub** all past `expenses.json` versions from history + force-push |
| Categorization | **Deterministic** Plaid-category → 7-category map + vendor overrides (no AI) |

## Current architecture (as-is)

- `python-scripts/expense-tracker/main.py` runs every ~30 min via
  `.github/workflows/expense-sync.yml`.
- Flow: Gmail candidate emails → Claude Haiku extraction → filter to current month →
  exclude non-budget vendors → category overrides → dedup (alert-vs-receipt, then
  vs. manual app entries) → **write two places**:
  - `web-apps/payday-checklist/expenses.json` (committed to the repo, fetched by the app), and
  - **Firestore** `households/gray/transactions/{email_id}` via `firestore_writer.py`
    (create-only, so user edits/deletes are never overwritten).
- The web app (`index.html` + `sync.js`) uses **IndexedDB** as the local UI store and
  **Firestore** as the cross-device backend when signed in. It fetches `expenses.json`
  only as a **signed-out fallback** delivery pipe — redundant on any signed-in device.
- Firestore security rules already lock all reads/writes to Gray's **verified** Google
  account (`graydavis33@gmail.com`). This is the private boundary; the public
  `firebase-config.js` web keys are public by design.

## Target architecture

### Components

1. **`plaid_client.py`** — thin wrapper over the Plaid SDK:
   - create a Link token, exchange a `public_token` → `access_token`,
   - `/transactions/sync` (cursor-based incremental pull: `added` / `modified` / `removed`).
2. **`plaid_sync.py`** (new module, invoked from `main.py`) — pull → filter → map →
   dedup → write Plaid transactions to Firestore.
3. **`connect_bank.py`** (one-time, local, Windows) — runs the Plaid Link browser flow
   once, captures the read-only `access_token`, and writes it **straight into the
   `PLAID_ACCESS_TOKEN` GitHub Actions secret via API** (never to a repo file, never
   printed). Also the definitive test that Plaid supports PrimeSouth.
4. **`category_map.py`** — deterministic Plaid `personal_finance_category` → the app's
   7 budget categories, plus a small vendor-override table (reuses the existing
   `CATEGORY_OVERRIDES` idea). Unknown → `Misc`.
5. **`firestore_writer.py` additions** — write Plaid docs (`source:"plaid"`, doc id =
   Plaid `transaction_id`, create-only); read/write an opaque **sync cursor** doc at
   `households/gray/plaid_state/cursor`.
6. **Workflow (`expense-sync.yml`) changes** — add `PLAID_CLIENT_ID`, `PLAID_SECRET`,
   `PLAID_ACCESS_TOKEN` secrets; **remove** the `expenses.json` commit step; run the
   scanner in **quiet mode** (counts only).
7. **App change** — stop fetching `./expenses.json` (delete the fallback path). The app
   already has Firestore as its source of truth when signed in.
8. **History scrub** — purge `expenses.json` from all history with `git filter-repo`,
   force-push, re-clone on the Mac. Separate, explicitly-gated phase.

### Recurring data flow (every ~30 min, existing workflow)

1. **Plaid** `/transactions/sync` from the stored cursor →
   `added` / `modified` / `removed`.
2. **Filter to real purchases.** Exclude, by Plaid category, anything that is not
   discretionary spending: income/credits, internal transfers, loan payments, rent,
   and Edward Jones movements (the EJ email parser owns those, with the tax/invest split).
3. **Map** each kept transaction to one of the 7 categories (deterministic table +
   vendor overrides; unknown → `Misc`).
4. **Dedup vs. manual** app entries (reuse `dedupe_vs_manual`: amount within a cent,
   dates within 2 days; manual tombstones suppress too).
5. **Write to Firestore** (`source:"plaid"`, id = `transaction_id`, create-only).
   Handle `modified` (pending → posted amount changes) and `removed` (a pending
   transaction Plaid later drops) so pending + posted never double-count.
6. **Gmail backstop** runs after Plaid: its expenses dedup against **all non-Gmail
   Firestore records** — which now includes the Plaid transactions — via the existing
   `dedupe_vs_manual` mechanism, so a purchase captured by Plaid suppresses its Gmail
   receipt automatically. No new cross-source dedup code required.
7. **Edward Jones** email parser is unchanged (tax/invest transfers → EJ card).
8. **No `expenses.json` written.** The signed-in app receives everything live from
   Firestore.

### Pending vs. posted

`/transactions/sync` surfaces **pending** transactions immediately (this is what would
have caught the missed same-day purchase), then reconciles them: a pending item is
later returned in `removed` and the posted item arrives in `added` with its own stable
`transaction_id`. Keying Firestore docs on `transaction_id` plus honoring `removed`
(tombstone the dropped pending doc) prevents any double-count.

## Privacy & security (the hard requirement)

- **Firestore is the only home for financial data.** Rules require Gray's verified
  Google account for every read and write. Confirmed in `firestore.rules`.
- **`expenses.json` is fully retired:** scanner stops writing it → file untracked and
  added to `.gitignore` → **all 193 historical versions scrubbed from git history**
  with `git filter-repo`, then force-push. The Mac clone re-clones afterward; the
  auto-commit hooks are paused during the rewrite.
  - Honest limitation: history scrubbing removes the data from the repo and its history
    going forward, but cannot guarantee that no third party already cloned or that
    GitHub's own caches purge instantly. It closes the ongoing leak; it can't rewrite
    the past for anyone who already copied it.
- **CI logs carry no money.** The scanner detects the CI context (or defaults to quiet)
  and prints **counts only** — never vendor, amount, or category totals. A test asserts
  the CI-mode output contains no `$`/amount-shaped strings.
- **Plaid credentials are Actions secrets** (`PLAID_CLIENT_ID`, `PLAID_SECRET`,
  `PLAID_ACCESS_TOKEN`), encrypted, never committed, never printed. The access token is
  **read-only (Transactions scope)** — worst-case exposure is read access to transaction
  history, not money movement.
- **The one-time connect flow** writes the token directly to the secret via API; any
  temporary artifact stays in the scratchpad dir and is deleted. Local runs read
  `PLAID_*` from a gitignored `.env` (already covered by the `.env` ignore pattern).
- **The sync cursor** is an opaque pagination token (non-sensitive) stored in Firestore,
  not in the repo.

## Categorization

Plaid returns a `personal_finance_category` (primary + detailed) per transaction. A
deterministic table maps the primary category to one of: `Groceries`, `Dining`,
`Software & Tools`, `Utilities`, `Investments`, `BJJ & Kickboxing`, `Misc`. A small
vendor-override table handles known merchants that the generic category gets wrong.
Anything unmapped falls to `Misc`. Gray can recategorize any transaction in the app;
because writes are create-only, the scanner never reverts his change.

## Testing

- **Unit tests** (offline, no network): category mapping; purchase-vs-exclude filtering
  by Plaid category; sign handling (Plaid depository amounts: positive = outflow);
  dedup across Plaid/Gmail/manual; pending→posted reconciliation (`removed` handling).
- **Plaid Sandbox** integration: exercise `connect_bank` + `/transactions/sync` against
  Plaid's sandbox institution (test data, no real bank) before touching Production.
- **Dry-run mode** (no Firestore writes) for the first real Production pull — eyeball
  the data before anything is written.
- **Privacy assertions:** a test that CI-mode stdout contains no financial strings;
  after the scrub, `git log -- web-apps/payday-checklist/expenses.json` returns empty
  and the file 404s on GitHub.

## Cutover phases (safe order)

1. Build + unit-test Plaid modules; verify against Plaid **Sandbox**. No writes.
2. `connect_bank.py`: connect **PrimeSouth** in Production → capture read-only token →
   store as secret. **Confirms PrimeSouth coverage** (the one real unknown).
3. First Production pull in **dry-run**; eyeball transactions + categories.
4. Flip the scanner live: Plaid → Firestore; **stop writing `expenses.json`**; silence
   CI logs; keep Gmail as a deduped backstop; EJ parser unchanged.
5. Point the app off `expenses.json` (remove the fetch).
6. **Scrub git history** of `expenses.json` + force-push; re-clone on Mac. _(explicitly
   gated on Gray's go — already approved.)_
7. Gray signs into the app on **iPhone** → confirm Plaid transactions appear on the phone
   (the long-pending cross-device smoke test).

Phases 1–4 are independently reversible. Phase 6 is the irreversible one.

## Risks / open items

- **PrimeSouth coverage** is unconfirmed until Phase 2. If Plaid doesn't support it,
  fall back to SimpleFIN Bridge or manual CSV import (the app already imports CSV).
- **Plaid re-auth:** banks periodically force re-login (`ITEM_LOGIN_REQUIRED`). Need a
  re-connect path (re-run `connect_bank.py`); surface a clear signal when it happens.
- **History rewrite** disrupts the Mac clone (must re-clone) and briefly the auto-commit
  hooks. One-time cost, scheduled deliberately.
- **Prior exposure** of the already-committed data can't be fully un-leaked (see Privacy
  note). The scrub stops it going forward.
- **Plaid Trial plan terms** could change; monitor that 1 connected account stays free.
