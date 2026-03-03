"""
invoice_generator.py
Builds a PDF invoice using ReportLab, saves it to ~/Desktop/Invoices/,
emails it to the client, and logs it to Google Sheets.
"""

import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

from config import (
    INVOICE_OUTPUT_DIR,
    YOUR_NAME,
    YOUR_TITLE,
    INVOICE_DUE_DAYS,
)
from sheets_client import (
    get_next_invoice_number,
    append_invoice,
    append_line_items,
)
from gmail_client import get_gmail_service, send_invoice_email


def collect_invoice_details():
    """
    Interactive CLI prompts to gather invoice information from Gray.
    Returns a dict with all the data needed to build the invoice.
    """
    print("\n" + "=" * 50)
    print("  Create New Invoice")
    print("=" * 50)

    client_name = input("\n  Client name: ").strip()
    client_email = input("  Client email: ").strip()

    print("\n  Add line items. Type 'done' when finished.\n")

    line_items = []
    while True:
        description = input("  Service description (or 'done'): ").strip()
        if description.lower() == "done":
            break

        charge_type = input("  Charge type — (1) Flat fee  (2) Hourly: ").strip()

        if charge_type == "2":
            hours = float(input("  Hours: ").strip())
            rate = float(input("  Hourly rate ($): ").strip())
            subtotal = round(hours * rate, 2)
            line_items.append({
                "description": description,
                "hours": hours,
                "rate": rate,
                "flat_fee": "",
                "subtotal": subtotal,
            })
            print(f"  Added: {hours}h × ${rate}/hr = ${subtotal:.2f}\n")
        else:
            flat_fee = float(input("  Flat fee ($): ").strip())
            line_items.append({
                "description": description,
                "hours": "",
                "rate": "",
                "flat_fee": flat_fee,
                "subtotal": flat_fee,
            })
            print(f"  Added: ${flat_fee:.2f}\n")

    if not line_items:
        print("  No line items entered. Cancelling.")
        return None

    total = round(sum(item["subtotal"] for item in line_items), 2)
    today = datetime.today()
    due_date = today + timedelta(days=INVOICE_DUE_DAYS)

    print(f"\n  Total: ${total:.2f}")
    confirm = input("  Generate and send this invoice? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return None

    return {
        "client_name": client_name,
        "client_email": client_email,
        "line_items": line_items,
        "total": total,
        "date": today.strftime("%Y-%m-%d"),
        "due_date": due_date.strftime("%Y-%m-%d"),
    }


def build_pdf(invoice_num, details):
    """
    Generate the invoice PDF and save it to INVOICE_OUTPUT_DIR.
    Returns the full path to the saved PDF.
    """
    os.makedirs(INVOICE_OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(INVOICE_OUTPUT_DIR, f"Invoice_{invoice_num}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # ─── Header ───────────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph(f"<b>INVOICE</b>", ParagraphStyle("h1", fontSize=22, fontName="Helvetica-Bold")),
            Paragraph(f"<b>#{invoice_num}</b>", ParagraphStyle("inv_num", fontSize=16, alignment=TA_RIGHT)),
        ]
    ]
    header_table = Table(header_data, colWidths=[4 * inch, 3 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2 * inch))

    # ─── From / To ────────────────────────────────────────────────────────────
    from_to_data = [
        [
            Paragraph(f"<b>{YOUR_NAME}</b><br/>{YOUR_TITLE}", styles["Normal"]),
            Paragraph(
                f"Date: {details['date']}<br/>Due: {details['due_date']}",
                ParagraphStyle("dates", alignment=TA_RIGHT)
            ),
        ],
        [
            Paragraph(
                f"<b>Bill To:</b><br/>{details['client_name']}<br/>{details['client_email']}",
                styles["Normal"]
            ),
            "",
        ],
    ]
    from_to_table = Table(from_to_data, colWidths=[4 * inch, 3 * inch])
    from_to_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(from_to_table)
    story.append(Spacer(1, 0.3 * inch))

    # ─── Services Table ───────────────────────────────────────────────────────
    table_data = [["Description", "Hours", "Rate", "Amount"]]

    for item in details["line_items"]:
        hours = f"{item['hours']}" if item.get("hours") else "—"
        rate = f"${item['rate']}/hr" if item.get("rate") else "—"
        subtotal = f"${item['subtotal']:.2f}"
        table_data.append([item["description"], hours, rate, subtotal])

    # Summary total row
    table_data.append(["", "", "TOTAL", f"${details['total']:.2f}"])

    col_widths = [3.5 * inch, 0.8 * inch, 1.0 * inch, 1.2 * inch]
    services_table = Table(table_data, colWidths=col_widths)
    services_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        # Body rows
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Total row
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("ALIGN", (2, -1), (-1, -1), "RIGHT"),
    ]))
    story.append(services_table)
    story.append(Spacer(1, 0.4 * inch))

    # ─── Footer ───────────────────────────────────────────────────────────────
    footer = Paragraph(
        "Thank you for your business!",
        ParagraphStyle("footer", fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
    )
    story.append(footer)

    doc.build(story)
    return pdf_path


def create_invoice():
    """
    Full invoice creation flow:
    1. Collect details via CLI prompts
    2. Get next invoice number from Sheets
    3. Build PDF
    4. Email to client
    5. Log to Google Sheets
    """
    details = collect_invoice_details()
    if not details:
        return

    print("\n  Generating invoice...")

    invoice_num = get_next_invoice_number()
    pdf_path = build_pdf(invoice_num, details)
    print(f"  PDF saved: {pdf_path}")

    # Send email
    print(f"  Sending to {details['client_email']}...")
    service = get_gmail_service()
    send_invoice_email(
        service,
        to_email=details["client_email"],
        client_name=details["client_name"],
        invoice_num=invoice_num,
        total=details["total"],
        pdf_path=pdf_path,
    )
    print("  Email sent.")

    # Log to Sheets
    append_invoice(
        invoice_num=invoice_num,
        client=details["client_name"],
        client_email=details["client_email"],
        date=details["date"],
        due_date=details["due_date"],
        status="Sent",
        total=details["total"],
    )
    append_line_items(invoice_num, details["line_items"])
    print(f"  Logged to Google Sheets.")

    print(f"\n  Done! Invoice #{invoice_num} — ${details['total']:.2f} sent to {details['client_name']}.")
