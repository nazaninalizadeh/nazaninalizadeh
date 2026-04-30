"""
Ricevuta (Receipt/Invoice) PDF Generator.
Design based on Housing in Padova brand template.
"""

from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from pathlib import Path

LOGO_PATH = Path(__file__).parent.parent / "uploads" / "logo_consulenze.jpg"

# Italian number-to-words converter for amounts
UNITS = ['', 'uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove']
TEENS = ['dieci', 'undici', 'dodici', 'tredici', 'quattordici', 'quindici', 'sedici', 'diciassette', 'diciotto', 'diciannove']
TENS = ['', 'dieci', 'venti', 'trenta', 'quaranta', 'cinquanta', 'sessanta', 'settanta', 'ottanta', 'novanta']
HUNDREDS = ['', 'cento', 'duecento', 'trecento', 'quattrocento', 'cinquecento', 'seicento', 'settecento', 'ottocento', 'novecento']

def _number_to_italian(n):
    if n == 0:
        return 'zero'
    if n < 0:
        return 'meno ' + _number_to_italian(-n)
    result = ''
    if n >= 1000:
        thousands = n // 1000
        if thousands == 1:
            result += 'mille'
        else:
            result += _number_to_italian(thousands) + 'mila'
        n %= 1000
    if n >= 100:
        result += HUNDREDS[n // 100]
        n %= 100
    if n >= 20:
        tens_digit = n // 10
        ones_digit = n % 10
        ten_word = TENS[tens_digit]
        if ones_digit in (1, 8):
            ten_word = ten_word[:-1]
        result += ten_word
        if ones_digit > 0:
            result += UNITS[ones_digit]
    elif n >= 10:
        result += TEENS[n - 10]
    elif n > 0:
        result += UNITS[n]
    return result


def generate_ricevuta_pdf(data: dict) -> BytesIO:
    """
    Generate a professional Ricevuta (Receipt) PDF matching Housing in Padova design.
    
    data keys:
    - receipt_number, date, time, amount
    - recipient_name (tenant name)
    - description_lines (list of up to 3 description strings)
    - note (optional footer text)
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    elems = []

    # Custom styles
    brand_style = ParagraphStyle('Brand', parent=styles['Normal'], fontSize=24, textColor=colors.HexColor('#9F1239'), fontName='Helvetica-Oblique', alignment=TA_CENTER, spaceAfter=2*mm)
    tagline_style = ParagraphStyle('Tag', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#555555'), alignment=TA_CENTER, fontName='Helvetica', letterSpacing=2)
    addr_style = ParagraphStyle('Addr', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#777777'), alignment=TA_CENTER, spaceAfter=4*mm)
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#888888'))
    value_style = ParagraphStyle('Value', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold')
    amount_big = ParagraphStyle('AmtBig', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#9F1239'), fontName='Helvetica-Bold', alignment=TA_RIGHT)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#AAAAAA'), alignment=TA_CENTER)

    amount = data.get('amount', 0)
    receipt_number = data.get('receipt_number', '')
    date_str = data.get('date', datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    time_str = data.get('time', datetime.now(timezone.utc).strftime('%H:%M'))
    recipient = data.get('recipient_name', '')
    desc_lines = data.get('description_lines', [])
    note = data.get('note', '')

    # Amount in words
    amount_int = int(amount)
    cents = int(round((amount - amount_int) * 100))
    amount_words = _number_to_italian(amount_int)
    amount_written = f"{amount_words}/{cents:02d} euro"

    # ========== HEADER ==========
    # Logo
    if LOGO_PATH.exists():
        try:
            logo = Image(str(LOGO_PATH), width=4*cm, height=2.5*cm)
            logo.hAlign = 'CENTER'
            elems.append(logo)
        except Exception:
            pass

    elems.append(Paragraph("Housing in Padova", brand_style))
    elems.append(Paragraph("AFFITTA &bull; COMPRA &bull; VENDE &bull; RISTRUTTURA &bull; APPARTAMENTI", tagline_style))
    elems.append(Paragraph("VIA VIGONOVESE 114", addr_style))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0B8A3E"), spaceAfter=6*mm))

    # ========== RECEIPT INFO ==========
    info_data = [
        [
            Paragraph("RICEVUTA n.", label_style),
            Paragraph("data", label_style),
            Paragraph("ore", label_style),
            Paragraph("importo", label_style),
        ],
        [
            Paragraph(str(receipt_number), value_style),
            Paragraph(date_str, value_style),
            Paragraph(time_str, value_style),
            Paragraph(f"\u20ac {amount:,.2f}", amount_big),
        ],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 4*cm, 3*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    elems.append(info_table)
    elems.append(Spacer(1, 6*mm))

    # ========== RICEVUTO DA ==========
    elems.append(Paragraph("Ricevuto da", label_style))
    elems.append(Paragraph(f"<b>{recipient}</b>", ParagraphStyle('RecipName', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold', spaceAfter=4*mm)))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB"), spaceAfter=4*mm))

    # ========== EURO LINE ==========
    euro_data = [
        [
            Paragraph("\u20ac", ParagraphStyle('Euro', parent=styles['Normal'], fontSize=18, textColor=colors.HexColor('#9F1239'), fontName='Helvetica-Bold')),
            Paragraph(amount_written, ParagraphStyle('Written', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#2C1810'), fontName='Helvetica-Oblique')),
        ]
    ]
    euro_table = Table(euro_data, colWidths=[1.5*cm, 15.5*cm])
    euro_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elems.append(euro_table)
    elems.append(Spacer(1, 4*mm))

    # ========== PER LINES ==========
    elems.append(Paragraph("<b>Per</b>", ParagraphStyle('PerLabel', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#9F1239'), spaceAfter=2*mm)))

    for i, line in enumerate(desc_lines[:3]):
        if line:
            elems.append(Paragraph(f"<b>riga {i+1}:</b>  {line}", ParagraphStyle('PerLine', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#2C1810'), spaceAfter=2*mm, leftIndent=10)))

    if not desc_lines:
        elems.append(Paragraph(f"Affitto di mese ({amount:,.2f} ({amount_words} euro))\u20ac", ParagraphStyle('PerLine', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#2C1810'), spaceAfter=2*mm, leftIndent=10)))

    elems.append(Spacer(1, 8*mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB"), spaceAfter=4*mm))

    # ========== NOTE ==========
    if note:
        elems.append(Paragraph(f"<i>Testo finale: {note}</i>", ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#888888'), spaceAfter=6*mm)))

    # ========== FOOTER ==========
    elems.append(Spacer(1, 15*mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD"), spaceAfter=3*mm))
    elems.append(Paragraph("Housing in Padova — by Consulenze Immobiliari | Documento generato automaticamente", footer_style))
    now = datetime.now(timezone.utc)
    elems.append(Paragraph(f"Generato il {now.strftime('%d/%m/%Y alle %H:%M')} UTC", footer_style))

    doc.build(elems)
    buf.seek(0)
    return buf
