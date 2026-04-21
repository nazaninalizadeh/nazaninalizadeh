"""
Hospitality (Ospitalità) PDF Generator.
COMUNICAZIONE DI OSPITALITA' IN FAVORE DI CITTADINO EXTRACOMUNITARIO
Based on the real Italian government form (Art. 7 D.Lvo 25 luglio 1998 Nr. 286).
"""

from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def _field_cell(label, value, width=None):
    """Create a label/value cell pair for the form."""
    return [label, value or ""]


def generate_hospitality_pdf(data: dict) -> BytesIO:
    """Generate COMUNICAZIONE DI OSPITALITA' PDF."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.2*cm, bottomMargin=1*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elems = []

    # Styles
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=13, textColor=colors.black, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=1*mm, leading=16)
    subtitle_s = ParagraphStyle('ST', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#333333'), alignment=TA_CENTER, spaceAfter=4*mm)
    section_s = ParagraphStyle('Sec', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#9F1239'), fontName='Helvetica-Bold', spaceAfter=2*mm, spaceBefore=4*mm)
    label_s = ParagraphStyle('L', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#666666'), fontName='Helvetica')
    val_s = ParagraphStyle('V', parent=styles['Normal'], fontSize=10, textColor=colors.black, fontName='Helvetica-Bold')
    small_s = ParagraphStyle('Sm', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#555555'), leading=9)
    legal_s = ParagraphStyle('Legal', parent=styles['Normal'], fontSize=6, textColor=colors.HexColor('#666666'), leading=8, spaceAfter=3*mm)

    # ========== TITLE ==========
    elems.append(Paragraph("COMUNICAZIONE DI OSPITALIT&Agrave;", title_s))
    elems.append(Paragraph("IN FAVORE DI CITTADINO EXTRACOMUNITARIO", ParagraphStyle('T2', parent=title_s, fontSize=11, spaceAfter=1*mm)))
    elems.append(Paragraph("(ARTICOLO 7 DEL DECRETO LEGISLATIVO 25 LUGLIO 1998 NR. 286)", subtitle_s))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#9F1239"), spaceAfter=4*mm))

    # ========== SECTION 1: DICHIARANTE (Host) ==========
    elems.append(Paragraph("IL SOTTOSCRITTO (DICHIARANTE)", section_s))

    host = [
        ["Cognome:", data.get("host_surname", ""), "Nome:", data.get("host_name", "")],
        ["Data di nascita:", data.get("host_dob", ""), "Comune di nascita:", data.get("host_birth_place", "")],
        ["Provincia:", data.get("host_province", ""), "", ""],
        ["Residenza:", data.get("host_residence", ""), "", ""],
    ]
    ht = Table(host, colWidths=[3*cm, 5.5*cm, 3.5*cm, 6*cm])
    ht.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#444')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (1, 0), (1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEBELOW', (3, 0), (3, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('SPAN', (1, 2), (3, 2)), ('SPAN', (1, 3), (3, 3)),
    ]))
    elems.append(ht)
    elems.append(Spacer(1, 3*mm))

    # ========== DURATION ==========
    elems.append(Paragraph("ai sensi dell'art. 7 del D.lvo nr. 286/98, DICHIARA CHE", small_s))

    check_in = data.get("check_in_date", "")
    check_out = data.get("check_out_date", "")
    duration_text = f"DAL <b>{check_in}</b>"
    if check_out:
        duration_text += f"  &nbsp; E FINO AL <b>{check_out}</b>"
    else:
        duration_text += "  &nbsp; E A TEMPO INDETERMINATO"
    elems.append(Paragraph(duration_text, ParagraphStyle('Dur', parent=styles['Normal'], fontSize=9, spaceAfter=2*mm, spaceBefore=2*mm)))

    hosting_type = data.get("hosting_type", "alloggio")
    if hosting_type == "cessione":
        elems.append(Paragraph("[X] ha ceduto la propriet&agrave; o il godimento di beni immobili al Signor/alla Signora:", small_s))
    else:
        elems.append(Paragraph("[X] ha fornito alloggio / ospitalit&agrave; al Signor/alla Signora:", small_s))

    elems.append(Spacer(1, 3*mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=3*mm))

    # ========== SECTION 2: CESSIONARIO (Guest/Tenant) ==========
    elems.append(Paragraph("CESSIONARIO / CITTADINO EXTRACOMUNITARIO", section_s))

    guest = [
        ["Cognome:", data.get("guest_surname", ""), "Nome:", data.get("guest_name", "")],
        ["Data di nascita:", data.get("guest_dob", ""), "Comune di nascita:", data.get("guest_birth_place", "")],
        ["Provincia/Nazione:", data.get("guest_birth_nation", ""), "Cittadinanza:", data.get("guest_citizenship", "")],
        ["Residenza:", data.get("guest_residence", ""), "", ""],
    ]
    gt = Table(guest, colWidths=[3*cm, 5.5*cm, 3.5*cm, 6*cm])
    gt.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#444')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (1, 0), (1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEBELOW', (3, 0), (3, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('SPAN', (1, 3), (3, 3)),
    ]))
    elems.append(gt)
    elems.append(Spacer(1, 2*mm))

    # Document details
    doc_data = [
        ["Tipo documento:", data.get("doc_type", "PASSAPORTO"), "Nr. documento:", data.get("passport_number", "")],
        ["Data rilascio:", data.get("doc_issue_date", ""), "Autorit&agrave;:", data.get("doc_authority", "")],
    ]
    dt = Table(doc_data, colWidths=[3*cm, 5.5*cm, 3.5*cm, 6*cm])
    dt.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#444')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (1, 0), (1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEBELOW', (3, 0), (3, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    elems.append(dt)
    elems.append(Spacer(1, 3*mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=3*mm))

    # ========== SECTION 3: PROPERTY ==========
    elems.append(Paragraph("IMMOBILE SITO IN", section_s))

    prop = [
        ["Comune:", data.get("property_comune", ""), "Provincia:", data.get("property_provincia", "")],
        ["Via/Piazza:", data.get("property_address", ""), "Numero:", data.get("property_number", "")],
        ["Interno:", data.get("property_interno", ""), "Piano:", data.get("property_piano", "")],
    ]
    pt = Table(prop, colWidths=[3*cm, 5.5*cm, 3.5*cm, 6*cm])
    pt.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#444')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (1, 0), (1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEBELOW', (3, 0), (3, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    elems.append(pt)
    elems.append(Spacer(1, 8*mm))

    # ========== SIGNATURE ==========
    now = datetime.now(timezone.utc)
    sig = [
        [
            Paragraph(f"Luogo e data: {data.get('property_comune', '')} , {now.strftime('%d/%m/%Y')}", ParagraphStyle('SL', parent=styles['Normal'], fontSize=9)),
            Paragraph("", styles['Normal']),
            Paragraph("Firma del dichiarante", ParagraphStyle('SR', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#888'), alignment=TA_CENTER)),
        ],
        [
            Paragraph("", styles['Normal']),
            Paragraph("", styles['Normal']),
            Paragraph("_________________________________", ParagraphStyle('SigLine', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)),
        ],
    ]
    st = Table(sig, colWidths=[7*cm, 3*cm, 8*cm])
    st.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    elems.append(st)
    elems.append(Spacer(1, 6*mm))

    # ========== ALLEGATI ==========
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD"), spaceAfter=3*mm))
    elems.append(Paragraph("<b>ALLEGATI:</b>", ParagraphStyle('Att', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#444'), spaceAfter=1*mm)))
    allegati = [
        "- COPIA DI UN DOCUMENTO DEL DICHIARANTE",
        "- COPIA DEL PASSAPORTO O PERMESSO DI SOGGIORNO DEL CESSIONARIO",
        "- COPIA DELLA DOCUMENTAZIONE COMPROVANTE LA PROPRIET&Agrave; O CONTRATTO DI LOCAZIONE",
    ]
    for a in allegati:
        elems.append(Paragraph(a, legal_s))

    # ========== LEGAL TEXT ==========
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph(
        "<b>ARTICOLO 7 DEL DECRETO LEGISLATIVO 25 LUGLIO 1998 NR. 286:</b>",
        ParagraphStyle('LegalTitle', parent=styles['Normal'], fontSize=6, textColor=colors.HexColor('#555'), spaceAfter=1*mm)
    ))
    elems.append(Paragraph(
        "\"Chiunque, a qualsiasi titolo, d&agrave; alloggio ovvero ospita uno straniero o apolide, anche se parente o affine, "
        "o lo assume per qualsiasi causa alle proprie dipendenze ovvero cede allo stesso la propriet&agrave; o il godimento di "
        "beni immobili, rustici o urbani posti sul territorio dello Stato, &egrave; tenuto a darne comunicazione scritta, entro 48 "
        "ore, all'Autorit&agrave; locale di pubblica sicurezza. Le violazioni delle disposizioni di cui al presente articolo sono "
        "soggette alla sanzione amministrativa del pagamento di una somma da 160 a 1.100 &euro;.\"",
        legal_s
    ))

    doc.build(elems)
    buf.seek(0)
    return buf
