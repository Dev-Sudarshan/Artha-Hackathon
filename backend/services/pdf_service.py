from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.colors import HexColor
from datetime import datetime
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


def _draw_blockchain_verification_page(c, width, height, loan_id, blockchain_tx_hash, blockchain_loan_hash, approval_date=None):
    """
    Draws a blockchain verification page on the current canvas page.
    This page contains the loan ID, TX hash, and data hash for admin verification.
    """
    # Background header band
    c.setFillColor(HexColor("#1a237e"))
    c.rect(0, height - 55 * mm, width, 55 * mm, fill=1, stroke=0)

    # Title
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 20 * mm, "BLOCKCHAIN VERIFICATION CERTIFICATE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 30 * mm, "ARTHA P2P PLATFORM - Immutable Loan Record")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, height - 40 * mm, "This page certifies that the loan agreement has been recorded on the blockchain")

    # Reset fill color
    c.setFillColor(HexColor("#000000"))

    y = height - 75 * mm

    # Loan ID (large, prominent)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(25 * mm, y, "LOAN ID:")
    c.setFont("Courier-Bold", 14)
    c.setFillColor(HexColor("#1a237e"))
    c.drawString(55 * mm, y, str(loan_id))
    c.setFillColor(HexColor("#000000"))
    y -= 15 * mm

    # Approval date
    if approval_date:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(25 * mm, y, "Approval Date:")
        c.setFont("Helvetica", 11)
        c.drawString(65 * mm, y, str(approval_date))
        y -= 12 * mm

    # Divider
    c.setStrokeColor(HexColor("#1a237e"))
    c.setLineWidth(1.5)
    c.line(25 * mm, y, width - 25 * mm, y)
    y -= 12 * mm

    # Blockchain Transaction Hash
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "Blockchain Transaction Hash (TX Hash):")
    y -= 8 * mm
    c.setFont("Courier", 9)
    tx_display = str(blockchain_tx_hash) if blockchain_tx_hash else "Pending..."
    # Wrap long hash across lines
    for i in range(0, len(tx_display), 80):
        c.drawString(25 * mm, y, tx_display[i:i+80])
        y -= 6 * mm
    y -= 4 * mm

    # Blockchain Data Hash
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "Loan Data Hash (SHA-256):")
    y -= 8 * mm
    c.setFont("Courier", 9)
    hash_display = str(blockchain_loan_hash) if blockchain_loan_hash else "Pending..."
    for i in range(0, len(hash_display), 80):
        c.drawString(25 * mm, y, hash_display[i:i+80])
        y -= 6 * mm
    y -= 8 * mm

    # Divider
    c.setStrokeColor(HexColor("#1a237e"))
    c.line(25 * mm, y, width - 25 * mm, y)
    y -= 12 * mm

    # Verification instructions box
    c.setStrokeColor(HexColor("#455a64"))
    c.setLineWidth(0.5)
    box_top = y
    box_height = 50 * mm
    c.rect(25 * mm, y - box_height, width - 50 * mm, box_height, fill=0, stroke=1)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#1a237e"))
    c.drawString(28 * mm, y - 6 * mm, "HOW TO VERIFY THIS LOAN:")
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica", 9)

    instructions = [
        "1. Go to the Artha P2P Blockchain Explorer",
        f"2. Search for Loan ID: {loan_id}",
        "3. Or search using the TX Hash shown above",
        "4. The explorer will show the on-chain record matching this agreement",
        "5. Compare the Data Hash above with the hash shown in the explorer",
        "6. If both hashes match, the loan data has NOT been tampered with",
    ]
    iy = y - 14 * mm
    for inst in instructions:
        c.drawString(28 * mm, iy, inst)
        iy -= 6 * mm

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawCentredString(width / 2, 20 * mm, "This blockchain record is immutable and cannot be altered after creation.")
    c.drawCentredString(width / 2, 15 * mm, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.setFillColor(HexColor("#000000"))


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
    loan_id: str = None,
    blockchain_tx_hash: str = None,
    blockchain_loan_hash: str = None,
    approval_date: str = None,
    output_dir: str = "generated_pdfs",
):
    """
    Generates loan agreement PDF (A4, multi-page).
    Includes Loan ID on the first page.
    If blockchain hashes are provided, appends a Blockchain Verification page.
    Returns file path.
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

    # Loan ID prominently displayed
    if loan_id:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(HexColor("#1a237e"))
        c.drawCentredString(width / 2, height - 50 * mm, f"LOAN ID: {loan_id}")
        c.setFillColor(HexColor("#000000"))

    c.setFont("Helvetica", 11)
    y = height - 65 * mm

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

    # -------- THUMBPRINTS PAGE --------
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

    # -------- BLOCKCHAIN VERIFICATION PAGE (if hashes provided) --------
    if blockchain_tx_hash or blockchain_loan_hash:
        _draw_blockchain_verification_page(
            c, width, height,
            loan_id=loan_id,
            blockchain_tx_hash=blockchain_tx_hash,
            blockchain_loan_hash=blockchain_loan_hash,
            approval_date=approval_date,
        )
        c.showPage()

    c.save()

    return file_path


def regenerate_agreement_with_blockchain(
    loan_data: dict,
    blockchain_tx_hash: str,
    blockchain_loan_hash: str,
    approval_date: str = None,
    output_dir: str = "generated_pdfs",
) -> str:
    """
    Regenerates the loan agreement PDF with blockchain verification data.
    Called after admin approval when blockchain hashes are available.
    Returns the new file path.
    """
    # Extract borrower info from loan data
    basic_info = loan_data.get("basic_info", {})
    # Try multiple locations for borrower name
    borrower_name = loan_data.get("borrower_name", "")
    if not borrower_name:
        borrower_name = " ".join(filter(None, [
            basic_info.get("first_name", ""),
            basic_info.get("middle_name", ""),
            basic_info.get("last_name", ""),
        ]))
    if not borrower_name:
        borrower_name = loan_data.get("user_id", "N/A")

    borrower_cit_no = loan_data.get("borrower_citizenship_no", "N/A")
    if borrower_cit_no == "N/A":
        borrower_cit_no = loan_data.get("id_documents", {}).get("id_details", {}).get("id_number", "N/A")

    guarantor = loan_data.get("guarantor", {}) or {}
    guarantor_name = guarantor.get("full_name", "N/A") if isinstance(guarantor, dict) else "N/A"
    guarantor_cit = guarantor.get("citizenship_no", "N/A") if isinstance(guarantor, dict) else "N/A"

    return generate_loan_agreement_pdf(
        borrower_full_name=borrower_name,
        borrower_citizenship_no=borrower_cit_no,
        guarantor_full_name=guarantor_name,
        guarantor_citizenship_no=guarantor_cit,
        amount=loan_data.get("amount", 0),
        interest_rate=loan_data.get("interest_rate", 0),
        tenure_months=loan_data.get("tenure_months", 0),
        net_amount_received=loan_data.get("net_amount_received", 0),
        net_amount_returned=loan_data.get("total_payable", 0),
        loan_id=loan_data.get("loan_id", ""),
        blockchain_tx_hash=blockchain_tx_hash,
        blockchain_loan_hash=blockchain_loan_hash,
        approval_date=approval_date,
        output_dir=output_dir,
    )
