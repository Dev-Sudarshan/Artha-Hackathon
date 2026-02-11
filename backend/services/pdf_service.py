from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.enums import TA_JUSTIFY
import os
import textwrap
import uuid


RULES_AND_REGULATIONS = """
ARTICLE 1: LOAN STRUCTURE & REPAYMENT OBLIGATIONS
Lenders: Receive Rs. X principal investment at 13% declining balance interest over 12 months. Total return: Rs. XX (principal + Rs. X interest + fees). Fixed EMI: Rs. X due 5th monthly. 100% capital protection via Neco Insurance (90-day fallback).
Borrowers: Must repay Rs. X total (Rs. X × 12 months). Full EMI mandatory - NO partial payments. 5-day grace period maximum. EMI schedule: Month 1 (Rs. X) → Month 12 (Rs. X). Processing fee Rs. XX + insurance Rs. XX deducted upfront.

ARTICLE 2: ABSOLUTE REPAYMENT GUARANTEE
Lenders: IRREVOCABLE borrower commitment regardless of circumstances (job loss, medical emergency, business failure, natural disaster, bankruptcy).
Borrowers: UNCONDITIONALLY guarantee 100% repayment. NO EXCUSES clause.

ARTICLE 3: STRICT PAYMENT DISCIPLINE
Borrowers: FULL EMI or NOTHING. NO partial payments, NO payment holidays.

ARTICLE 4: PENALTY & DEFAULT TRIGGERS
Grace period: 5 days max. Penalties escalate daily.

ARTICLE 5: DEFAULT CONSEQUENCES & ENFORCEMENT
CIB blacklist, legal recovery, asset seizure.

ARTICLE 6: INSURANCE PROTECTION MECHANISM
Insurance protects lender only.

ARTICLE 7: MONITORING & VERIFICATION SYSTEM
AI monitoring, blockchain records.

ARTICLE 8: PERSONAL GUARANTEE & ASSET DECLARATION
Future income assignment, asset declaration.

ARTICLE 9: EXECUTION & IRREVOCABLE COMMITMENT
Digital signature, thumbprint, blockchain timestamp.

ARTICLE 10: JURISDICTION & LEGAL FRAMEWORK
Kathmandu DRT jurisdiction.

ARTICLE 11: GUARANTOR DEFINITION & ROLE
Guarantor is equally and severally liable.
"""


def generate_loan_agreement_pdf(
    borrower_full_name: str,
    borrower_citizenship_no: str,
    guarantor_full_name: str,
    guarantor_citizenship_no: str,
    amount: int,
    interest_rate: float,
    tenure_months: int,
    net_amount_received: float,
    net_amount_returned: float,
    output_dir: str = "generated_pdfs",
):
    """
    Generates unsigned loan agreement PDF (A4, multi-page)
    Returns file path
    """

    os.makedirs(output_dir, exist_ok=True)
    file_name = f"loan_agreement_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(output_dir, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    normal_style.alignment = TA_JUSTIFY

    # -------- PAGE 1 : TITLE & LOAN DETAILS --------
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 30 * mm, "ARTHA P2P PLATFORM")
    c.drawCentredString(width / 2, height - 40 * mm, "RULES AND REGULATIONS")

    c.setFont("Helvetica", 11)
    y = height - 60 * mm

    details = [
        f"Borrower Full Name: {borrower_full_name}",
        f"Borrower Citizenship ID No: {borrower_citizenship_no}",
        f"Guarantor Full Name: {guarantor_full_name}",
        f"Guarantor Citizenship ID No: {guarantor_citizenship_no}",
        f"Loan Amount: Rs. {amount}",
        f"Interest Rate: {interest_rate} %",
        f"Tenure: {tenure_months} months",
        f"Net Amount Received: Rs. {net_amount_received}",
        f"Net Amount Returned (if paid fully): Rs. {net_amount_returned}",
    ]

    for line in details:
        c.drawString(30 * mm, y, line)
        y -= 8 * mm

    # Borrower signature (first page)
    c.line(30 * mm, 40 * mm, 90 * mm, 40 * mm)
    c.drawString(30 * mm, 35 * mm, "Borrower Signature")

    c.showPage()

    # -------- RULES & REGULATIONS (MULTI-PAGE) --------
    text = c.beginText(25 * mm, height - 25 * mm)
    c.setFont("Helvetica", 10)

    for line in RULES_AND_REGULATIONS.split("\n"):
        wrapped = textwrap.wrap(line, 95)
        if not wrapped:
            text.textLine("")
        for w in wrapped:
            if text.getY() < 30 * mm:
                c.drawText(text)
                c.showPage()
                text = c.beginText(25 * mm, height - 25 * mm)
                c.setFont("Helvetica", 10)
            text.textLine(w)

    c.drawText(text)

    # Borrower signature on rules pages
    c.line(30 * mm, 30 * mm, 90 * mm, 30 * mm)
    c.drawString(30 * mm, 25 * mm, "Borrower Signature")

    c.showPage()

    # -------- FINAL PAGE : THUMBPRINTS --------
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 30 * mm, "THUMBPRINT CONFIRMATION")

    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 60 * mm, "Borrower Thumbprints:")
    c.rect(30 * mm, height - 90 * mm, 40 * mm, 30 * mm)
    c.rect(80 * mm, height - 90 * mm, 40 * mm, 30 * mm)
    c.drawString(30 * mm, height - 95 * mm, "Left Thumb")
    c.drawString(80 * mm, height - 95 * mm, "Right Thumb")

    c.drawString(30 * mm, height - 130 * mm, "Guarantor Thumbprints:")
    c.rect(30 * mm, height - 160 * mm, 40 * mm, 30 * mm)
    c.rect(80 * mm, height - 160 * mm, 40 * mm, 30 * mm)
    c.drawString(30 * mm, height - 165 * mm, "Left Thumb")
    c.drawString(80 * mm, height - 165 * mm, "Right Thumb")

    c.showPage()
    c.save()

    return file_path
