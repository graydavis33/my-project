# Gray — Finances Reference

_Last updated: 2026-07-30. This file is the source of truth for real-world money facts that
the Payday Checklist app does not store. It lives in the repo so it syncs Mac <-> Windows._

---

## Student loans — MOHELA (verified 2026-07-30)

All four are **federal Direct Unsubsidized** loans. Servicer: **MOHELA**
(myaccount.mohela.studentaid.gov). Prior servicer reference to "Nelnet" in a Plaid test fixture
is stale/wrong for these loans.

| Loan | Balance | Interest rate | Due date shown |
|---|---|---|---|
| 1-01 Direct Loan - Unsubsidized | $6,097.02 | 3.730% | 08/28/2026 |
| 1-02 Direct Loan - Unsubsidized | $7,443.82 | 4.990% | 08/28/2026 |
| 1-03 Direct Loan - Unsubsidized | $8,630.47 | 5.500% | 08/28/2026 |
| 1-04 Direct Loan - Unsubsidized | $8,369.41 | 6.530% | 08/28/2026 |
| **Total** | **$30,540.72** | **~5.31% weighted avg** | |

Roughly **$135/month** of interest accruing.

**IMPORTANT — the old "20% interest" figure was WRONG.** It drove the original decision to rank
loans above investing and to delete the Investments budget category. At ~5.3% that call is much
softer. Do not repeat the 20% number. Stale copies of it still need scrubbing from
`web-apps/payday-checklist/index.html` (step 3 sub-label) and `PAYDAY-SPEC-2026-07.md`.

**Payoff math (whole balance, ~5.31% blended):**
- $1,000/mo -> ~33 months, ~$2,360 total interest
- $750/mo -> ~45 months, ~$3,210 total interest
- Delta: cutting to $750 costs ~$850 and ~1 extra year.

**Payoff order (avalanche):** extra dollars to **1-04 (6.53%)**, then 1-03 (5.50%),
then 1-02 (4.99%). Minimum only on **1-01 (3.73%)** — it barely beats a high-yield savings rate.

### Open questions to confirm with MOHELA
- **Actual repayment start date.** Gray believes Oct 30 or Dec 30, 2026, but the portal shows a
  due date of **08/28/2026** on all four loans. Resolve before assuming an October start.
- **Does accrued interest capitalize at the end of the grace period?** If yes, paying accrued
  interest down before that date is worth extra.
- Every extra payment must be directed: **"apply to principal of loan 1-04, do not advance my
  due date."** Otherwise servicers commonly just push the due date forward.

### Prepayment facts (confirmed 2026-07-30)
- Federal student loans have **no prepayment penalty**.
- **Paying early does NOT move or forfeit the repayment start date.** Grace period end is set by
  when he left school, not by payment activity.
- Overpaying can put the account in **"paid ahead"** status — future bills pre-covered. A cushion,
  not a penalty.
- If income disappears, all safety nets remain available regardless of prepayment: unemployment
  deferment (up to 3 yrs), economic hardship deferment, forbearance, and income-driven repayment
  (can be $0/mo). Note interest **still accrues** on unsubsidized loans during deferment.

---

## Accounts and their roles

- **Edward Jones** — Sole Proprietor **TAX** account (30% of income). Do not touch.
  Gray's **uncle works at Edward Jones** and will keep any cash there out of the markets.
- **PrimeSouth** — everyday bank; its alert emails feed the Payday app's expense automation.
  Savings there has historically held the emergency fund + ring fund.
- **Emergency fund + ring fund** — should sit in a **high-yield savings account** (FDIC-insured,
  ~4%), not a brokerage, with two separate buckets. At a 3.73% cheapest loan rate there is no
  tension in holding cash. If the uncle can quote a competitive cash yield **net of any account
  fee and any advisory percentage fee**, Edward Jones is a fine home for the **ring fund**
  (fixed date, no rush). The **emergency fund** favors an HYSA purely for speed of access —
  brokerage withdrawals can take days plus a phone call.

---

## Monthly plan (as of 2026-07-30)

Monthly income $6,500 (2 x $3,250 bi-weekly), ~$4,550 after 30% tax.

| Line | Amount |
|---|---|
| Rent (**dropped from $1,900**) | $1,800 |
| Student loans | $1,000 |
| Emergency fund | $400 |
| Ring fund | $200 |
| **Investments (min $100/mo — standing rule)** | $100 |
| Budgets (Groceries 200 / Dining 150 / BJJ 200 / Software 100 / Utilities 60 / Misc 140) | $850 |
| **Leftover** | **$200** |

The $100 rent savings funds the investments line, so loans stay at $1,000 with no loss of cushion.

**Misc buffer rule:** whatever is left of the $140 Misc buffer at month end splits **50/50**
between the Ring Fund and Student Loans.

**Goals:** Emergency Fund $12,000 · Ring Fund $10,000.

### App changes still pending
- Rent default $1,900 -> $1,800.
- Re-add an Investments line ($100/mo) — the budget category was deleted 2026-07-17.
- Replace the "Attack the 20% interest" step sub-label with the real ~5.3% figure.
