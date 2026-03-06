"""
contract_template.py
Freelance video services contract template.
Edit the TEMPLATE string directly to update your contract terms.
Placeholders: {CLIENT_NAME}, {COMPANY}, {PROJECT_TYPE}, {SCOPE},
              {TIMELINE}, {BUDGET}, {YOUR_NAME}, {DATE}
"""

TEMPLATE = """FREELANCE VIDEO SERVICES AGREEMENT

This Agreement is entered into as of {DATE}, between {YOUR_NAME} ("Videographer")
and {CLIENT_NAME}{COMPANY_LINE} ("Client").

---

1. SERVICES

Videographer agrees to provide the following services:

Project Type: {PROJECT_TYPE}
Deliverables: {SCOPE}
Timeline: {TIMELINE}

---

2. COMPENSATION

Client agrees to pay Videographer ${BUDGET} for the services described above.

Payment Terms:
- 50% deposit due upon signing this agreement to reserve the date
- Remaining 50% due within 14 days of final delivery
- Payments accepted via Venmo, Zelle, or bank transfer

Late payments beyond 14 days are subject to a 5% monthly late fee.

---

3. REVISIONS

The project includes up to 2 rounds of revisions. Additional revisions will be billed
at Videographer's standard hourly rate.

---

4. USAGE RIGHTS

Upon receipt of full payment, Client receives a non-exclusive license to use the
delivered content for marketing, social media, and promotional purposes.
Videographer retains the right to display the work in their portfolio.

---

5. CANCELLATION

If Client cancels within 48 hours of a scheduled shoot, the deposit is non-refundable.
If Videographer cancels, the deposit will be refunded in full.

---

6. LIMITATION OF LIABILITY

Videographer's liability is limited to the total project fee. Videographer is not
responsible for any indirect, incidental, or consequential damages.

---

7. AGREEMENT

By signing below, both parties agree to the terms of this Agreement.

Client Signature: ________________________  Date: __________
Name: {CLIENT_NAME}

Videographer Signature: ________________________  Date: __________
Name: {YOUR_NAME}

---

Questions? Contact {YOUR_NAME} at graydavis33@gmail.com
"""


def render_contract(details: dict, your_name: str, date: str) -> str:
    """Fill in the contract template with client details."""
    company_line = f" ({details['company']})" if details.get('company') else ""
    return TEMPLATE.format(
        DATE=date,
        YOUR_NAME=your_name,
        CLIENT_NAME=details['client_name'],
        COMPANY_LINE=company_line,
        PROJECT_TYPE=details['project_type'],
        SCOPE=details['scope'],
        TIMELINE=details['timeline'],
        BUDGET=details['budget'],
    )
