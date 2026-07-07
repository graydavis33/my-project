# Payday Checklist Phase 2 — Gray's Handoff Checklist

Everything is built, tested (46 Phase 1 + 9 sync + 11 scanner tests green), and deployed **inert** — the app behaves exactly like before until you finish these steps. They take about 15 minutes total, all clicking, no code.

Spec: `docs/superpowers/specs/2026-07-07-payday-sync-and-expense-automation-design.md`

---

## A. Create the Firebase project (~10 min, one time)

1. Go to https://console.firebase.google.com — sign in as **graydavis33@gmail.com** → **Create a project** → name it `payday-checklist` → turn **Analytics OFF** → create.
2. **Build → Authentication → Get started** → *Sign-in method* tab → **Google** → Enable → save (pick graydavis33@gmail.com as support email).
3. **Authentication → Settings → Authorized domains** → **Add domain** → `graydavis33.github.io`.
4. **Build → Firestore Database → Create database** → Production mode → location `nam5 (United States)` → create.
5. Firestore → **Rules** tab → replace everything with the contents of `web-apps/payday-checklist/firestore.rules` → **Publish**.
6. Project settings (gear icon) → **Your apps** → Web (`</>` icon) → nickname `payday` → register (no hosting) → copy the `const firebaseConfig = {...}` object it shows you.
7. Open `web-apps/payday-checklist/firebase-config.js` and replace `null` with that object (or just paste the object into a Claude session and say "wire in the payday firebase config"). Commit + push.
8. Project settings → **Service accounts** → **Generate new private key** → downloads a JSON file.
9. GitHub → `graydavis33/my-project` → **Settings → Secrets and variables → Actions → New repository secret** → name `FIREBASE_SERVICE_ACCOUNT` → paste the ENTIRE contents of that JSON file → save. Then delete the downloaded JSON file.

## B. PrimeSouth card alerts (~2 min)

Your Zelle-send alerts already flow in (verified live). What's missing is **debit-card purchase alerts**:

1. PrimeSouth mobile app → card management/alerts → **Transaction Alerts** → enable, threshold **$0 / all transactions**, delivery **EMAIL** (to graydavis33@gmail.com).
2. If email delivery isn't offered (push-only), tell Claude — fallback options are already scoped (Plaid/SimpleFIN or bank CSV import).
3. Rocket Money is already emailing large/uncategorized transaction alerts and those are parsed too. If you want fuller Rocket coverage: Rocket Money app → Settings → Notifications → turn on email for new transactions (if offered).

## C. Live smoke test (~5 min, after A)

1. On Windows: open the app → **Export Backup** first (safety net).
2. The budgets card now shows a "sign in" link at the bottom → sign in with graydavis33@gmail.com → status should flip to "✓ synced".
3. iPhone: open the installed PWA → same sign-in → your Windows data should appear.
   - If Google sign-in won't open inside the installed app: open the site in Safari, sign in there once, then use the PWA again (or reinstall it).
4. Add a "test $1" expense on the phone → watch it appear on Windows within seconds. Delete it on Windows → gone from the phone.
5. Airplane-mode the phone → add an expense → reconnect → it shows up on Windows.
6. Buy a coffee. Within ~30–90 min it should appear on both devices (from the receipt email or card alert). Delete it once if you don't want it counted.

## D. Tell Claude when smoke test passes

Next session after C works, say "payday smoke test passed" and Claude will do the cutover: retire `expenses.json` + the dismissed-list (Firestore becomes the only path) and log the completion.

---

## Notes / known behaviors

- **"Reset Everything" while synced** only clears the device — cloud data re-syncs back. To truly wipe, delete the docs in Firebase console (or ask Claude to add a cloud-wipe button if you want one).
- **Restoring a CSV backup while synced**: transactions you'd previously deleted stay deleted (the cloud remembers tombstones). Everything else restores normally.
- The `firebase-config.js` values are **safe to commit** — Firebase web configs are public by design; the Firestore rules (email-locked) are the security boundary.
- Scanner runs every 30 min now (was daily 7am). GitHub delays crons under load, so effective cadence is ~30–90 min.
- Large Rocket Money alerts (e.g. an $8,400 Edward Jones transfer) will land in Investments/Misc and can swamp a budget row — just delete/dismiss them in the app; they won't come back.
