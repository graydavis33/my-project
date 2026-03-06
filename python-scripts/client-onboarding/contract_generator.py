"""
contract_generator.py
Generates a PDF contract using ReportLab and saves it to OUTPUT_DIR.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

from config import OUTPUT_DIR, YOUR_NAME
from contract_template import render_contract


def generate_contract_pdf(details: dict) -> str:
    """
    Generate the contract PDF and save to OUTPUT_DIR.
    Returns the full path to the saved PDF.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = details['client_name'].replace(' ', '_')
    filename = f"Contract_{safe_name}_{datetime.today().strftime('%Y%m%d')}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, filename)

    date_str = datetime.today().strftime("%B %d, %Y")
    contract_text = render_contract(details, YOUR_NAME, date_str)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "body",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "heading",
        parent=styles["Normal"],
        fontSize=12,
        leading=18,
        fontName="Helvetica-Bold",
        spaceAfter=6,
        spaceBefore=12,
    )
    center_style = ParagraphStyle(
        "center",
        parent=styles["Normal"],
        fontSize=14,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    story = []

    # Split contract text into paragraphs
    lines = contract_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.1 * inch))
        elif stripped.startswith("FREELANCE VIDEO SERVICES"):
            story.append(Paragraph(stripped, center_style))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 0.05 * inch))
        elif stripped[0].isdigit() and ". " in stripped[:4]:
            story.append(Paragraph(stripped, heading_style))
        else:
            story.append(Paragraph(stripped, body_style))

    doc.build(story)
    return pdf_path
