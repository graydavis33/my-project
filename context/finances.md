# Gray — Finances Reference

_Last updated: 2026-07-30. This file is the source of truth for real-world money facts that
the Payday Checklist app does not store. It lives in the repo so it syncs Mac <-> Windows._

---

## Student loans — MOHELA (verified 2026-07-30)

All four are **federal Direct Unsubsidized** loans. Servicer: **MOHELA**
(myaccount.mohela.studentaid.gov). Prior servicer reference to "Nelnet" in a Plaid test fixture
is stale/wrong for these loans.

All four fully captured 2026-07-30. School: University of Georgia. Owner: US Dept of Education.
Interest accrued through 07/30/2026 on all four. All fixed-rate. Due date shown: 08/28/2026.

| Loan | Principal | **Unpaid interest** | Balance | Rate |
|---|---|---|---|---|
| 1-01 Direct - Unsubsidized | $5,500.00 | $597.02 | $6,097.02 | 3.730% |
| 1-02 Direct - Unsubsidized | $6,500.00 | $943.82 | $7,443.82 | 4.990% |
| 1-03 Direct - Unsubsidized | $7,500.00 | $1,130.47 | $8,630.47 | 5.500% |
| 1-04 Direct - Unsubsidized | $7,500.00 | $869.41 | $8,369.41 | 6.530% |
| **Total** | **$27,000.00** | **$3,540.72** | **$30,540.72** | **~5.31% wtd avg** |

Roughly **$135/month** of interest accruing. Borrowed $27,000; the other $3,540.72 is accrued
deferment interest.

**Required minimum once repayment starts: ~$330/mo** (Level, 10 yr, ~$30.5k at 5.31%). Gray's
$1,000/mo plan is ~3x the minimum — big slack if income ever drops.

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

### STATUS: unemployment deferment ending 09/11/2026 (from loan 1-04 detail page)

Gray is **NOT in a grace period.** Loan 1-04's detail page shows:

| Field | Value |
|---|---|
| Loan Status | **Unemployment Deferment — Ends 09/11/2026** |
| Repayment Start Date | 10/29/2025 (already passed) |
| Repayment Plan | Level — Ends 08/28/2036 |
| Estimated Payoff Date | 08/28/2036 (standard 10-yr at MINIMUM payments — not his plan) |
| Unpaid Principal | $7,500.00 |
| **Unpaid Interest** | **$869.41** |
| Current Balance | $8,369.41 |
| Interest Type | Fixed, 6.530% |
| Interest Accrued Through | 07/30/2026 |
| Loan/Borrower Benefits | Interest Rate Reduction – DI01 (likely the 0.25% autopay discount) |

**THE DEADLINE IS 09/11/2026.** Unsubsidized interest accrued through the whole deferment and
typically **capitalizes** (folds into principal) when a deferment ends. Payments apply to accrued
interest before principal, so every dollar sent before 9/11 reduces what capitalizes 1:1.

Exact exposure: **$3,540.72** capitalizes on 9/11/2026 if unpaid. Cost of letting all of it
capitalize is roughly **$250–300** over a ~3-year payoff. Worth capturing, NOT worth draining the
emergency fund over.

At $1,000/mo the real payoff is ~mid-2029 (~33 months), not 2036. At $750/mo, ~45 months.

### Pre-9/11 payment order (rate-first; payments hit accrued interest before principal)

| Order | Target | Amount |
|---|---|---|
| 1 | 1-04 accrued interest (6.53%) | $869.41 |
| 2 | 1-03 accrued interest (5.50%) | $1,130.47 |
| 3 | 1-02 accrued interest (4.99%) | $943.82 |
| 4 | 1-01 accrued interest (3.73%) | $597.02 |

Steps 1+2 total **$1,999.88** — reachable from ~2 months of the normal $1,000 loan allocation
with no savings touched. That clears capitalization on both high-rate loans. The remaining
$1,540.84 sits on the two cheapest loans and costs only ~$70/yr if it capitalizes.

Payment instruction to use every time: **"Apply to loan 1-04 until its accrued interest is paid,
then loan 1-03. Do not advance my due date."**

### DI01 autopay discount — ACTION REQUIRED
Loan/Borrower Benefit "Interest Rate Reduction - DI01" status is **"Elig"** (eligible, not active).
Fine print: 0.25% reduction for authorizing automatic debit, **suspended during deferment or
forbearance** — which is why it is inactive now. **Set up autopay so it is live the day repayment
begins.** Worth ~$70/yr.

### Open questions to confirm with MOHELA
- **Does accrued interest capitalize when this deferment ends 9/11/2026?**
- **Is the DI01 autopay discount actually active?** If not, enrolling is a free 0.25%.
- **What is the monthly payment once repayment begins?** (Portal also shows a due date of
  08/28/2026 on all four loans — reconcile that against the 9/11 deferment end.)
- **Is the unemployment deferment still valid?** Gray is earning $6,500/mo; unemployment
  deferment generally requires being unemployed or working <30 hrs/week. Don't lean on it.
- Every extra payment must be directed: **"apply to accrued interest, then principal on loan
  1-04 — do not advance my due date."** Otherwise servicers commonly just push the due date.

### Action list
1. Set up **autopay** now (0.25% DI01 discount, live when repayment starts).
2. Send **~$2,000 before 9/11/2026**, directed to 1-04 then 1-03 accrued interest.
3. Call MOHELA: confirm capitalization on 9/11, and confirm the **unemployment deferment is still
   valid** — Gray earns $6,500/mo and that deferment generally requires unemployment or <30 hrs/wk.

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
