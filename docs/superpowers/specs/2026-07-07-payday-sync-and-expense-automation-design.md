# Payday Checklist — Cross-Device Sync + Full Expense Automation (Phase 2)

**Date:** 2026-07-07
**Status:** Approved (Gray approved Approach A verbally; waived spec review — "do what you gotta do, don't involve me")
**Builds on:** `web-apps/payday-checklist/PAYDAY-SPEC-2026-07.md` (Phase 1, shipped 2026-07-06)

---

## Goal

1. **Cross-device sync** — iPhone PWA and Windows browser share one dataset: transactions, settings, checklist steps, fund balances, dismissals. Change on one device, see it on the other.
2. **Full expense capture** — every dollar spent lands in the checklist automatically: email receipts (already live) + card swipes that never generate a receipt email (new), with swipe-to-checklist latency of ~30 minutes instead of up to 24 hours.

## Decisions Made (with Gray, 2026-07-07)

| Decision | Choice | Why |
|---|---|---|
| Sync backend | **Firebase (Firestore + Google sign-in)** | Zero maintenance, free tier, real-time, battle-tested conflict/offline plumbing. VPS rejected: needs domain+TLS+hand-rolled auth+backup story. |
| Card-swipe capture | **PrimeSouth per-transaction alert emails → existing Gmail scanner** | No third party holds bank creds; rides live pipeline. Plaid/SimpleFIN held in reserve if alerts prove unreliable or email delivery unsupported. |
| Architecture | **Approach A: Firestore = single source of truth** | Scanner writes Firestore directly; `expenses.json` retired after cutover. One data path; dismissals/edits sync properly. |
| Scan cadence | **Every 30 min** (was daily 7am) | Repo is public → Actions minutes free. GitHub may delay/skip cron under load; acceptable. |

## Architecture

```
Gmail (receipts + PrimeSouth card alerts)
        │  every 30 min (GitHub Action)
        ▼
expense-tracker (Python + Haiku extraction)
        │  firebase-admin, service account
        ▼
   Firestore  ◄──── real-time, two-way ────►  App on iPhone / Windows
   users/{uid}/…                              (IndexedDB stays the UI's local store,
                                               sync layer reconciles both directions)
```

### Data model (Firestore)

- `users/{uid}/transactions/{txnId}`
  - Fields: `date, vendor, amount, category, note, source ('manual'|'gmail'|'csv'), email_id?, deleted (bool), created_at, updated_at`
  - **Doc ID = `email_id` for gmail-source txns** (dedup for free), UUID for manual.
  - **Deletes are tombstones** (`deleted: true`), never document removal — this replaces the `dismissed_gmail` list: scanner uses `create()` semantics (skip if doc exists), so a dismissed receipt can never resurrect.
- `users/{uid}/settings/{key}`
  - One doc per settings key (`income, allocations, budgets, fund, ring, steps, notes, overrides`), fields `value, updated_at`.
  - Conflict rule everywhere: **last-write-wins by `updated_at`** (client clock; fine for a one-person app).

### Auth & security

- Firebase Auth, Google provider. `signInWithPopup`, fall back to `signInWithRedirect` (iOS standalone PWA quirk).
- Firestore security rules: `request.auth.uid == uid` **and** `request.auth.token.email == 'graydavis33@gmail.com'`. Nobody else can read/write, even with the (intentionally public) web config.
- Firebase web config is not a secret — committed as `firebase-config.js` once the project exists.

### Client sync layer (`sync.js`, new file)

- **Feature-flagged by config presence:** if `firebase-config.js` is absent/empty, the app runs exactly as Phase 1 (local-only). Safe to deploy before the Firebase project exists.
- IndexedDB remains what the UI reads/writes (no UI rewrite). The sync layer:
  - hooks every local mutation → mirrors to Firestore (SDK queues offline)
  - subscribes to Firestore snapshots → applies remote changes to IndexedDB → refreshes UI
  - **first sign-in migration:** existing local data uploads to Firestore (merge, LWW)
- Firebase JS SDK **self-hosted in the repo** (not CDN) so the service worker caches it and offline keeps working.
- Sign-in UI: small sync status row (signed out / syncing / synced / offline) + Google button; invisible legacy behavior when unconfigured.

### Scanner changes (`python-scripts/expense-tracker/`)

- New `firestore_writer.py`: firebase-admin, service account from `FIREBASE_SERVICE_ACCOUNT` env (GitHub secret). `create()` per txn, doc ID = email_id; AlreadyExists → skip.
- **Graceful degradation:** no service account → keep writing `expenses.json` exactly as today (zero breakage before Gray creates the project). After verified cutover, `expenses.json` path retires.
- Gmail query broadened: add bank-alert senders (PrimeSouth sender domain TBD — confirmed after Gray forwards one alert; keep an easily-edited `ALERT_SENDERS` list in `config.py`). Haiku prompt extended to parse bank purchase alerts (merchant, amount, date; category from existing rules).
- `--dry-run` flag: print what would be written, write nothing.
- Workflow `expense-sync.yml`: cron `*/30 * * * *`, `concurrency` group to prevent overlapping runs, service-account secret wired but optional.

## Error handling

- App offline → Firestore SDK queues writes; IndexedDB keeps UI live (unchanged from Phase 1).
- Sign-in fails / rules reject → app stays local-only, sync row shows error; no data loss.
- Scanner Firestore write fails → falls back to expenses.json write for that run + non-zero exit so the Action shows red.
- Clock skew between devices: LWW by client `updated_at` — acceptable single-user risk, documented.

## Testing

1. **Playwright e2e (extends the rescued 46-test suite, now living in-repo):** all Phase 1 tests stay green; new sync tests run two browser contexts against the **Firebase emulator** — add/appear, dismiss/vanish, offline-queue/reconnect, LWW conflict, first-sign-in migration. If emulator prerequisites (Node/Java) are unavailable on the machine, sync tests run against a scripted Firestore fake; emulator is preferred.
2. **Scanner fixtures:** canned receipt + bank-alert emails → assert parsed fields + Firestore writes (emulator) + dedup on re-run + dry-run writes nothing.
3. **Live smoke (Gray, at his leisure):** CSV export first → sign in both devices → $1 test expense phone→Windows realtime → airplane-mode roundtrip → real coffee with alerts on → appears both devices ≤30 min → dismiss once, gone everywhere.

## Rollout order

1. Rescue e2e suite into repo; keep green.
2. App sync layer behind config flag → deploy (inert).
3. Scanner: Firestore writer + alert parsing + dry-run, secret-optional → deploy (inert until secret exists).
4. Cron bump to 30 min (independent, immediate latency win for existing Gmail receipts).
5. **Gray's handoff (only human steps):** create Firebase project + enable Auth/Firestore + paste web config; add `FIREBASE_SERVICE_ACCOUNT` GitHub secret; flip on PrimeSouth per-transaction alerts (verify email delivery, $0 threshold); forward one alert email so the parser/senders list gets locked.
6. Cutover: verify live smoke → retire expenses.json path + `dismissed_gmail`.

## Out of scope (explicitly)

- Plaid/SimpleFIN integration (reserve — only if alerts miss transactions in practice)
- Multi-user/household support
- Firebase Hosting / Cloud Functions (app stays on GitHub Pages, scanner stays Python-on-Actions)
