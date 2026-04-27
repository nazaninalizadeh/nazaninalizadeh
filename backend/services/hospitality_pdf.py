"""COMUNICAZIONE DI OSPITALITA' PDF generator.

Matches the official Italian government template (Articolo 7 D.Lvo 25 luglio 1998
nr. 286). Black & white, no extra branding. Layout mirrors the scanned template
the user provided: a thick title bar at the top, DICHIARANTE / CITTADINO
EXTRACOMUNITARIO section tags in the left margin, GG MM AA date boxes, two
checkbox lines for "alloggio / ospitalità" vs "ceduto la proprietà", explicit
"E A TEMPO INDETERMINATO" checkbox, and the ALLEGATI + Articolo 7 footer.
"""

from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ---------- helpers ----------
def _split_date(d: str) -> tuple[str, str, str]:
    """'2025-12-01' or '01/12/2025' -> ('01','12','2025'). Empty -> ('','','')."""
    if not d:
        return "", "", ""
    s = d.strip()
    if "-" in s and len(s) >= 10:
        try:
            return s[8:10], s[5:7], s[:4]
        except Exception:
            pass
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
    return "", "", ""


def _label(text: str, size: int = 6, color: str = "#444444") -> Paragraph:
    return Paragraph(
        f'<font size="{size}" color="{color}"><i>{text}</i></font>',
        ParagraphStyle("lbl", fontName="Helvetica-Oblique", fontSize=size, leading=size + 2),
    )


def _val(text: str, size: int = 10) -> Paragraph:
    return Paragraph(
        f'<font size="{size}"><b>{(text or "").upper()}</b></font>',
        ParagraphStyle("val", fontName="Helvetica-Bold", fontSize=size, leading=size + 2),
    )


def _field(label: str, value: str) -> Table:
    """Underlined value with the field name in small italic below."""
    inner = Table([[_val(value)], [_label(label)]], colWidths=["100%"])
    inner.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 0.6, colors.HexColor("#777")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return inner


def _date_boxes(d: str) -> Table:
    day, mo, yr = _split_date(d)
    yr_short = yr[2:] if len(yr) == 4 else yr
    cells = Table(
        [[_val(day, 10), _val(mo, 10), _val(yr_short, 10)],
         [_label("GG"), _label("MM"), _label("AA")]],
        colWidths=[0.95 * cm, 0.95 * cm, 0.95 * cm],
    )
    cells.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 0.6, colors.black),
        ("BOX", (1, 0), (1, 0), 0.6, colors.black),
        ("BOX", (2, 0), (2, 0), 0.6, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    return cells


def _checkbox(checked: bool) -> Paragraph:
    glyph = "&#9745;" if checked else "&#9744;"
    return Paragraph(
        f'<font size="11">{glyph}</font>',
        ParagraphStyle("cb", fontName="Helvetica", fontSize=11, leading=12),
    )


def _section_tag(text: str) -> Paragraph:
    """Black tag used as a left-margin section label (DICHIARANTE / CITTADINO EXTRACOMUNITARIO)."""
    return Paragraph(
        f'<font size="8" color="white"><b>&nbsp;&nbsp;{text}&nbsp;&nbsp;</b></font>',
        ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=8, leading=11,
                       backColor=colors.black, textColor=colors.white,
                       borderPadding=(2, 4, 2, 4)),
    )


def _section_tag_table(text: str) -> Table:
    """Render a black-filled cell with white text — used as a left side tag."""
    t = Table(
        [[Paragraph(f'<font color="white" size="8"><b>{text}</b></font>',
                    ParagraphStyle("ss", fontName="Helvetica-Bold", fontSize=8,
                                   leading=10, alignment=TA_CENTER))]],
        colWidths=[3.6 * cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return t


# ---------- main ----------
def generate_hospitality_pdf(data: dict) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=0.8 * cm, bottomMargin=0.8 * cm,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    elems: list = []

    body_s = ParagraphStyle("Bd", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=9, leading=12, alignment=TA_LEFT)
    legal_s = ParagraphStyle("Lg", parent=styles["Normal"], fontName="Helvetica",
                             fontSize=6.5, leading=9, textColor=colors.HexColor("#222"))

    # ===== TITLE BAR (black filled) =====
    title_bar = Table(
        [[Paragraph(
            '<font color="white" size="13"><b>COMUNICAZIONE DI OSPITALIT&Agrave;</b></font><br/>'
            '<font color="white" size="10"><b>IN FAVORE DI CITTADINO EXTRACOMUNITARIO</b></font><br/>'
            '<font color="white" size="8">(ARTICOLO 7 DEL DECRETO LEGISLATIVO 25 LUGLIO 1998 NR. 286)</font>',
            ParagraphStyle("tt", alignment=TA_CENTER, leading=14, fontName="Helvetica"),
        )]],
        colWidths=[18.6 * cm],
    )
    title_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elems.append(title_bar)
    elems.append(Spacer(1, 4 * mm))

    # ===== DICHIARANTE block =====
    elems.append(Paragraph("Il sottoscritto", body_s))
    elems.append(Spacer(1, 2 * mm))

    host_block = [
        # row of section-tag + content tables
        [_section_tag_table("DICHIARANTE"),
         Table(
             [[_field("(Cognome)", data.get("host_surname", "")),
               _field("(Nome)", data.get("host_name", ""))]],
             colWidths=[7.5 * cm, 7.0 * cm],
             style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]),
         )],
    ]
    ht = Table(host_block, colWidths=[3.7 * cm, 14.6 * cm])
    ht.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elems.append(ht)
    elems.append(Spacer(1, 2 * mm))

    # date + birthplace + province
    elems.append(Table(
        [[_label("(Data di nascita)"), _label("(Comune di nascita)"), _label("(Provincia o nazione estera)")]],
        colWidths=[3.3 * cm, 9.0 * cm, 5.9 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]),
    ))
    elems.append(Table(
        [[_date_boxes(data.get("host_dob", "")),
          _field("", data.get("host_birth_place", "")),
          _field("", data.get("host_province", ""))]],
        colWidths=[3.3 * cm, 9.0 * cm, 5.9 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    ))
    elems.append(Spacer(1, 2 * mm))

    elems.append(_field("(Residenza - Comune, provincia, via o piazza, nr. civico)",
                        data.get("host_residence", "")))
    elems.append(Spacer(1, 4 * mm))

    # ===== Duration =====
    elems.append(Paragraph(
        "ai sensi dell'art. 7 del D.lvo nr. 286/98, <b>DICHIARA CHE DAL</b>", body_s))
    elems.append(Spacer(1, 1 * mm))

    is_indef = (not data.get("check_out_date"))
    duration = Table(
        [[_date_boxes(data.get("check_in_date", "")),
          Paragraph("<b>E FINO AL</b>", body_s),
          _date_boxes(data.get("check_out_date", "")),
          Paragraph("<b>oppure</b>", body_s),
          _checkbox(is_indef),
          Paragraph("<b>A TEMPO INDETERMINATO</b>", body_s)]],
        colWidths=[3.3 * cm, 1.9 * cm, 3.3 * cm, 1.5 * cm, 0.6 * cm, 7.6 * cm],
    )
    duration.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    elems.append(duration)
    elems.append(Spacer(1, 4 * mm))

    # Two header checkbox lines
    hosting_type = (data.get("hosting_type") or "alloggio").lower()
    is_alloggio = hosting_type != "cessione"
    elems.append(Table(
        [[_checkbox(is_alloggio),
          Paragraph("ha fornito <b>alloggio / ospitalit&agrave;</b> al Signor / alla Signora:", body_s)]],
        colWidths=[0.6 * cm, 18.0 * cm],
        style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                          ("LEFTPADDING", (0, 0), (-1, -1), 0)]),
    ))
    elems.append(Table(
        [[_checkbox(not is_alloggio),
          Paragraph("ha ceduto la <b>propriet&agrave; o il godimento di beni immobili</b>, "
                    "rustici o urbani al Signor / alla Signora:", body_s)]],
        colWidths=[0.6 * cm, 18.0 * cm],
        style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                          ("LEFTPADDING", (0, 0), (-1, -1), 0)]),
    ))
    elems.append(Spacer(1, 3 * mm))

    # ===== CITTADINO EXTRACOMUNITARIO block =====
    guest_top = Table(
        [[_section_tag_table("CITTADINO EXTRACOMUNITARIO"),
          Table(
              [[_field("(Cognome)", data.get("guest_surname", "")),
                _field("(Nome)", data.get("guest_name", ""))]],
              colWidths=[7.5 * cm, 7.0 * cm],
              style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                ("VALIGN", (0, 0), (-1, -1), "TOP")]),
          )]],
        colWidths=[3.7 * cm, 14.6 * cm],
    )
    guest_top.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elems.append(guest_top)
    elems.append(Spacer(1, 2 * mm))

    elems.append(Table(
        [[_label("(Data di nascita)"), _label("(Comune di nascita)"), _label("(Provincia o nazione estera)")]],
        colWidths=[3.3 * cm, 9.0 * cm, 5.9 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]),
    ))
    elems.append(Table(
        [[_date_boxes(data.get("guest_dob", "")),
          _field("", data.get("guest_birth_place", "")),
          _field("", data.get("guest_birth_nation", ""))]],
        colWidths=[3.3 * cm, 9.0 * cm, 5.9 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    ))
    elems.append(Spacer(1, 2 * mm))

    elems.append(_field("(Cittadinanza)", data.get("guest_citizenship", "")))
    elems.append(Spacer(1, 2 * mm))

    elems.append(_field("(Residenza - Comune, provincia, via o piazza, nr. civico)",
                        data.get("guest_residence", "")))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Table(
        [[_field("(Tipo documento)", data.get("doc_type", "PASSAPORTO")),
          _field("(Nr. documento)", data.get("passport_number", ""))]],
        colWidths=[7.5 * cm, 10.7 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    ))
    elems.append(Spacer(1, 2 * mm))

    elems.append(_field("(Autorit&agrave; che ha rilasciato il documento)",
                        data.get("doc_authority", "")))
    elems.append(Spacer(1, 2 * mm))

    elems.append(Table(
        [[_label("(Data di rilascio)")]], colWidths=[3.3 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]),
    ))
    elems.append(Table(
        [[_date_boxes(data.get("doc_issue_date", ""))]],
        colWidths=[3.3 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]),
    ))
    elems.append(Spacer(1, 5 * mm))

    # ===== Property =====
    elems.append(Paragraph(
        "La presente dichiarazione viene resa in qualit&agrave; di proprietario / intestatario "
        "dell'immobile sito in:", body_s))
    elems.append(Spacer(1, 2 * mm))

    elems.append(Table(
        [[_field("(Comune)", data.get("property_comune", "")),
          _field("(Provincia)", data.get("property_provincia", ""))]],
        colWidths=[12.5 * cm, 5.7 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    ))
    elems.append(Spacer(1, 2 * mm))

    elems.append(Table(
        [[_field("(Via o piazza)", data.get("property_address", "")),
          _field("(Numero civico)", data.get("property_number", "")),
          _field("(Interno)", data.get("property_interno", "")),
          _field("(Piano)", data.get("property_piano", ""))]],
        colWidths=[8.5 * cm, 3.5 * cm, 2.8 * cm, 3.4 * cm],
        style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    ))
    elems.append(Spacer(1, 8 * mm))

    # ===== Signature =====
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    luogo = data.get("property_comune", "") or (data.get("host_residence", "").split(",")[0] if data.get("host_residence") else "")
    sig = Table(
        [[Paragraph(f"Luogo e data: <b>{(luogo or '').upper()}, {today}</b>", body_s),
          Paragraph("firma del dichiarante",
                    ParagraphStyle("sg", fontName="Helvetica", fontSize=8, alignment=TA_CENTER,
                                   textColor=colors.HexColor("#444")))],
         ["",
          Paragraph("____________________________________",
                    ParagraphStyle("sl", fontName="Helvetica", fontSize=10, alignment=TA_CENTER))]],
        colWidths=[10.0 * cm, 8.2 * cm],
    )
    sig.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                             ("TOPPADDING", (0, 0), (-1, -1), 1),
                             ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elems.append(sig)
    elems.append(Spacer(1, 5 * mm))

    # ===== ALLEGATI =====
    sep = Table([[""]], colWidths=[18.6 * cm])
    sep.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.HexColor("#888"))]))
    elems.append(sep)
    elems.append(Spacer(1, 2 * mm))

    elems.append(Paragraph("<b>ALLEGATI:</b>", legal_s))
    for line in [
        "&#9744; COPIA DI UN DOCUMENTO DEL DICHIARANTE",
        ("&#9744; COPIA DI UN DOCUMENTO DEL CESSIONARIO (COPIA DEL PERMESSO DI SOGGIORNO IN CORSO DI VALIDIT&Agrave; "
         "O COPIA DEL PASSAPORTO PAGINA DEI DATI ANAGRAFICI E DEL VISTO D'INGRESSO UNITAMENTE A FOTOCOPIA RICEVUTA "
         "ASSICURATA DELLE POSTE)"),
        ("&#9744; COPIA DELLA DOCUMENTAZIONE COMPROVANTE LA PROPRIET&Agrave; O IL TITOLO DI GODIMENTO DELL'IMMOBILE "
         "(ATTO DI PROPRIET&Agrave;, CONTRATTO DI LOCAZIONE, ECC.)"),
        "&#8226; IL MODULO DEVE ESSERE SPEDITO CON RACCOMANDATA A/R IN DUE COPIE CON FIRMA IN ORIGINALE (TRATTENERE UNA TERZA COPIA)",
    ]:
        elems.append(Paragraph(line, legal_s))

    elems.append(Spacer(1, 2 * mm))
    elems.append(sep)
    elems.append(Spacer(1, 2 * mm))

    elems.append(Paragraph("<b>ARTICOLO 7 DEL DECRETO LEGISLATIVO 25 LUGLIO 1998 NR. 286:</b>", legal_s))
    elems.append(Paragraph(
        "&laquo;Chiunque, a qualsiasi titolo, d&agrave; alloggio ovvero ospita uno straniero o apolide, "
        "anche se parente o affine, o lo assume per qualsiasi causa alle proprie dipendenze ovvero cede "
        "allo stesso la propriet&agrave; o il godimento di beni immobili, rustici o urbani posti sul "
        "territorio dello Stato, &egrave; tenuto a darne comunicazione scritta, entro 48 ore, "
        "all'Autorit&agrave; locale di pubblica sicurezza. Le violazioni delle disposizioni di cui al "
        "presente articolo sono soggette alla sanzione amministrativa del pagamento di una somma da "
        "160 a 1.100 &euro;.&raquo;", legal_s))

    doc.build(elems)
    buf.seek(0)
    return buf
