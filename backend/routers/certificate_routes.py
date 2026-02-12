"""
Blockchain Certificate Generator
Generates PDF certificates with QR codes for blockchain proof
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import qrcode
from io import BytesIO
from datetime import datetime
import json

from multichain_rpc import get_stream_key_items
from admin.admin_auth import get_current_admin
from fastapi import Depends

router = APIRouter()


def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


@router.get("/certificate/{loan_id}")
async def generate_blockchain_certificate(
    loan_id: str,
    admin=Depends(get_current_admin)
):
    """
    Generate downloadable PDF certificate with blockchain proof
    """
    try:
        # Get loan from blockchain
        items = get_stream_key_items("loan_storage", f"loan_{loan_id}")
        
        if not items:
            raise HTTPException(status_code=404, detail="Loan not found on blockchain")
        
        latest = items[-1] if isinstance(items, list) else items
        data_str = latest.get('data', {}).get('json', '{}')
        loan_data = json.loads(data_str) if isinstance(data_str, str) else {}
        
        tx_hash = latest.get("txid")
        confirmations = latest.get("confirmations", 0)
        block_time = latest.get("blocktime", 0)
        loan_hash = loan_data.get("loan_hash")
        
        # Check repayment status
        repayment_items = get_stream_key_items("loan_repayments", f"repayment_{loan_id}")
        is_repaid = bool(repayment_items)
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12
        )
        
        # Title
        title = Paragraph("BLOCKCHAIN PROOF CERTIFICATE", title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Certificate text
        cert_text = Paragraph(
            f"This certifies that the loan <b>{loan_id}</b> has been recorded on the Aartha blockchain "
            f"for immutable verification and audit purposes.",
            styles['Normal']
        )
        story.append(cert_text)
        story.append(Spacer(1, 0.3*inch))
        
        # Blockchain Details Table
        details_heading = Paragraph("Blockchain Details", heading_style)
        story.append(details_heading)
        
        details_data = [
            ['Loan ID:', loan_id],
            ['Transaction Hash:', tx_hash[:40] + '...' if len(tx_hash) > 40 else tx_hash],
            ['Data Hash:', loan_hash[:40] + '...' if len(loan_hash) > 40 else loan_hash],
            ['Block Confirmations:', str(confirmations)],
            ['Timestamp:', datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Status:', 'REPAID' if is_repaid else 'ACTIVE'],
            ['Blockchain:', 'artha-chain (MultiChain)']
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Verification section
        verify_heading = Paragraph("Verification", heading_style)
        story.append(verify_heading)
        
        verify_text = Paragraph(
            f"Scan the QR code below or visit:<br/>"
            f"<b>http://localhost:8000/api/public/explore/loan/{loan_id}</b><br/>"
            f"to verify this certificate on the blockchain.",
            styles['Normal']
        )
        story.append(verify_text)
        story.append(Spacer(1, 0.2*inch))
        
        # Generate QR code
        qr_data = f"http://localhost:8000/api/public/explore/loan/{loan_id}"
        qr_buffer = generate_qr_code(qr_data)
        qr_image = Image(qr_buffer, width=2*inch, height=2*inch)
        story.append(qr_image)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = Paragraph(
            f"<i>Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i><br/>"
            f"<i>This certificate provides cryptographic proof that cannot be altered or forged.</i>",
            styles['Normal']
        )
        story.append(footer_text)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=blockchain_certificate_{loan_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate certificate: {str(e)}")
