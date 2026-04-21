"""
Hospitality (Ospitalità) PDF Template Generator.
Creates official guest registration documents.
"""

from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_hospitality_pdf(data: dict) -> BytesIO:
    """
    Generate a professional Ospitalità (Hospitality) PDF document.

    data keys:
    - tenant_name, passport_number, nationality, date_of_birth,
      gender, place_of_birth, passport_issue_date, passport_expiry_date,
      codice_fiscale
    - property_address, property_code, room_number, room_type
    - landlord_name, landlord_codice_fiscale
    - check_in_date, check_out_date
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elems = []

    # Custom styles
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=22, textColor=colors.HexColor("#1a1a2e"),
        alignment=TA_CENTER, spaceAfter=4 * mm,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER, spaceAfter=6 * mm,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#9F1239"),
        spaceAfter=3 * mm, spaceBefore=6 * mm,
        fontName="Helvetica-Bold",
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#777777"),
        fontName="Helvetica",
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )

    # Header
    elems.append(Paragraph("DICHIARAZIONE DI OSPITALIT&Agrave;", title_style))
    elems.append(Paragraph("Comunicazione di cessione di fabbricato", subtitle_style))
    elems.append(Paragraph(
        "Ai sensi dell'art. 12 del D.L. 21 marzo 1978, n. 59, convertito con modificazioni dalla L. 18 maggio 1978, n. 191",
        ParagraphStyle("Law", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER, spaceAfter=8 * mm),
    ))

    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#9F1239"), spaceAfter=6 * mm))

    # Document info
    now = datetime.now(timezone.utc)
    doc_number = f"OSP-{now.strftime('%Y%m%d')}-{data.get('tenant_name', 'X')[:3].upper()}"

    info_data = [
        [
            Paragraph("N. Documento", label_style),
            Paragraph("Data Emissione", label_style),
        ],
        [
            Paragraph(doc_number, value_style),
            Paragraph(now.strftime("%d/%m/%Y"), value_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[9 * cm, 8 * cm])
    info_table.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    elems.append(info_table)
    elems.append(Spacer(1, 4 * mm))

    # Section 1: Host/Landlord
    elems.append(Paragraph("DATI DEL DICHIARANTE (Ospitante)", section_style))
    host_data = [
        ["Nome e Cognome:", data.get("landlord_name", "-")],
        ["Codice Fiscale:", data.get("landlord_codice_fiscale", "-")],
        ["Indirizzo Immobile:", data.get("property_address", "-")],
        ["Codice Immobile:", data.get("property_code", "-")],
    ]
    host_table = Table(host_data, colWidths=[5 * cm, 12 * cm])
    host_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#444444")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1a1a2e")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    elems.append(host_table)
    elems.append(Spacer(1, 4 * mm))

    # Section 2: Guest/Tenant
    elems.append(Paragraph("DATI DELL'OSPITATO (Inquilino)", section_style))

    gender_map = {"M": "Maschio", "F": "Femmina"}
    gender_display = gender_map.get(data.get("gender", ""), data.get("gender", "-") or "-")

    guest_data = [
        ["Nome e Cognome:", data.get("tenant_name", "-")],
        ["Codice Fiscale:", data.get("codice_fiscale", "-")],
        ["Nazionalit&agrave;:", data.get("nationality", "-")],
        ["Data di Nascita:", data.get("date_of_birth", "-")],
        ["Luogo di Nascita:", data.get("place_of_birth", "-")],
        ["Sesso:", gender_display],
        ["N. Passaporto / Doc.:", data.get("passport_number", "-")],
        ["Data Rilascio:", data.get("passport_issue_date", "-")],
        ["Data Scadenza:", data.get("passport_expiry_date", "-")],
    ]
    guest_table = Table(guest_data, colWidths=[5 * cm, 12 * cm])
    guest_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#444444")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1a1a2e")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    elems.append(guest_table)
    elems.append(Spacer(1, 4 * mm))

    # Section 3: Accommodation Details
    elems.append(Paragraph("DATI DELL'ALLOGGIO", section_style))
    room_type_map = {"single": "Singola", "double": "Doppia"}
    accom_data = [
        ["Indirizzo:", data.get("property_address", "-")],
        ["Stanza N.:", data.get("room_number", "-")],
        ["Tipo Stanza:", room_type_map.get(data.get("room_type", ""), data.get("room_type", "-"))],
        ["Data Check-in:", data.get("check_in_date", "-")],
        ["Data Check-out:", data.get("check_out_date", "-")],
    ]
    accom_table = Table(accom_data, colWidths=[5 * cm, 12 * cm])
    accom_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#444444")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1a1a2e")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    elems.append(accom_table)
    elems.append(Spacer(1, 10 * mm))

    # Declaration text
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=4 * mm))
    declaration_text = (
        "Il/La sottoscritto/a dichiara, ai sensi dell'art. 12 del D.L. 21 marzo 1978, n. 59, "
        "di aver ceduto/ospitato la persona sopra indicata nell'immobile di cui sopra, "
        "impegnandosi a comunicare ogni eventuale variazione alle autorit&agrave; competenti."
    )
    elems.append(Paragraph(declaration_text, ParagraphStyle(
        "Decl", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#555555"),
        spaceAfter=12 * mm, leading=14,
    )))

    # Signature area
    sig_data = [
        [
            Paragraph("Data e Luogo", label_style),
            Paragraph("", label_style),
            Paragraph("Firma del Dichiarante", label_style),
        ],
        [
            Paragraph("_________________________", ParagraphStyle("Sig", parent=styles["Normal"], fontSize=10)),
            Paragraph("", styles["Normal"]),
            Paragraph("_________________________", ParagraphStyle("Sig", parent=styles["Normal"], fontSize=10, alignment=TA_RIGHT)),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[6 * cm, 5 * cm, 6 * cm])
    sig_table.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(sig_table)
    elems.append(Spacer(1, 15 * mm))

    # Footer
    elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD"), spaceAfter=3 * mm))
    elems.append(Paragraph(
        "Consulenze immobiliari - Via Vigonovese 114 | Documento generato automaticamente",
        footer_style,
    ))
    elems.append(Paragraph(
        f"Generato il {now.strftime('%d/%m/%Y alle %H:%M')} UTC",
        footer_style,
    ))

    doc.build(elems)
    buf.seek(0)
    return buf
