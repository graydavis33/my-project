# Invoice System — What Qualifies

## The Simple Rule
If money moved because of your business, it belongs here.
If it's personal (rent, groceries, personal Venmo to a friend), leave it out.

---

## INCOME — Money Coming In ✅

Money received counts if it came from:
- A client paying for a service (video editing, social media, content creation, etc.)
- A brand deal, sponsorship, or collaboration payment
- A retainer or recurring payment from a client
- A settlement or reimbursement related to a business matter (e.g. a legal case involving your work)
- Referral fees or commissions tied to your business

### Platforms that trigger automatic detection:
- **Venmo** — payment notifications from venmo.com
- **Zelle** — alerts from primesouthbank.com / email.primesouthbank.com
- **PayPal** — from paypal.com
- **Stripe** — from stripe.com
- **Cash App** — from cash.app or square.com
- **QuickBooks** — invoice paid notifications from quickbooks.intuit.com or intuit.com
- **Direct deposit** — bank notifications with "direct deposit" in subject

### What does NOT get auto-detected (add manually):
- Cash payments (hand-to-hand)
- Payments sent to a **different email account** (e.g. Robert's email, a second Gmail) — scanner only reads your primary Gmail
- Payments from platforms not listed above (e.g. wire transfer, check, Venmo to a different account)
- Payments where the email subject doesn't include keywords like "paid you", "you received", "payment from", etc.

### How to add manually:
```bash
cd ~/Desktop/my-project/python-scripts/invoice-system
python3 main.py add-expense   # use this for any manual entry
```
Or run a back-scan for a specific date range:
```bash
python3 main.py scan-payments --days 60
```

---

## BUSINESS EXPENSES — Money Going Out ✅

An expense counts if it was bought **for the business**, not personal use.

### Always include:
| Category | Examples |
|----------|---------|
| Software & Subscriptions | Adobe Creative Cloud, Canva, CapCut Pro, ChatGPT Plus, Notion, Dropbox |
| Equipment & Gear | Camera, lens, mic, hard drive, tripod, SD cards, laptop for work |
| Advertising & Marketing | Paid ads on Meta/TikTok/Google, boosted posts, sponsored placements |
| Contractor Payments | Paying an editor, a VA, a copywriter, another videographer |
| Other | Business meals (with a client), co-working space, printing, shipping |

### Always exclude (personal, not business):
- Rent, utilities, groceries, personal subscriptions (Netflix, Spotify, etc.)
- Venmo to friends/family for non-business reasons
- Personal clothing, personal travel not tied to a job

### Gray areas — use your judgment:
| Item | Rule of thumb |
|------|--------------|
| Phone bill | Only deduct the % used for business (e.g. 70% if mostly work) |
| Home internet | Only deduct the % used for business |
| Meal with a friend who is also a client | Counts if the conversation was about work |
| New laptop | Counts if primarily used for video/social work |

### Receipt emails that get auto-detected:
The system scans Gmail for receipts from common business vendors. For it to auto-detect, the email must land in your **primary Gmail** and include keywords like "receipt", "order confirmation", or "invoice".

---

## ABOUT ROBERT'S EMAIL / SECONDARY ACCOUNTS

The scanner **only reads the Gmail account linked in your .env file**.

If a payment (e.g. that $200 Venmo) goes to a **different email address**, it will never be auto-detected. You have two options:

1. **Manual entry** — run `python3 main.py scan-payments --days 60` on the Mac where that email is accessible, after authenticating that Gmail account. Or just add it manually.
2. **Long-term fix** — if Robert's email is also a Gmail, we can add a second Gmail account to the scanner in a future update.

---

## QUICK REFERENCE — Will It Be Auto-Detected?

| Scenario | Auto? | Action |
|----------|-------|--------|
| Venmo payment to your primary Gmail | ✅ Yes | Nothing needed |
| Zelle from PrimeSouth Bank email | ✅ Yes | Nothing needed |
| PayPal payment notification | ✅ Yes | Nothing needed |
| QuickBooks invoice paid | ✅ Yes | Nothing needed |
| Cash payment | ❌ No | Add manually |
| Payment to a different email account | ❌ No | Add manually or run back-scan on that account |
| Wire transfer / check | ❌ No | Add manually |
| Venmo payment where notification went to a second account | ❌ No | Add manually |
| Business expense receipt in primary Gmail | ✅ Yes | Nothing needed |
| Business expense paid in cash or card (no email) | ❌ No | Add manually |

---

## Running a Manual Back-Scan

If you know payments were missed, run this to re-scan the last 60 days:
```bash
cd ~/Desktop/my-project/python-scripts/invoice-system
python3 main.py scan-payments --days 60
python3 main.py scan-receipts --days 60
```

The system will skip anything already added (no duplicates).
