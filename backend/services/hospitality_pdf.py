"""COMUNICAZIONE DI OSPITALITA' PDF generator.

Drawn from scratch using ReportLab low-level primitives only:
  - canvas.rect() for every field box
  - canvas.line() for dividers and underlines
  - canvas.drawString() for all text
No flowables, no paragraph layout, no auto-formatting. Every coordinate is
fixed in absolute PDF points so the printed result matches the official
JALLAB Italian government form column-for-column.
"""

from io import BytesIO
from datetime import datetime, timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, white


PAGE_W, PAGE_H = A4   # 595.275 x 841.89 pt

# ---------- master grid ----------
LEFT = 28.0
RIGHT = PAGE_W - 28.0          # 567.275
TAG_W = 18.0                   # vertical "DICHIARANTE" tag column width
INNER_LEFT = LEFT + TAG_W      # 46.0
INNER_W = RIGHT - INNER_LEFT   # 521.275
LINE = 1.2                     # default border thickness


# ---------- helpers ----------
def _split_date(d: str) -> tuple[str, str, str]:
    if not d:
        return "", "", ""
    s = d.strip()
    if "-" in s and len(s) >= 10:
        return s[8:10], s[5:7], s[2:4]
    if "/" in s:
        p = s.split("/")
        if len(p) == 3:
            yr = p[2]
            return p[0], p[1], (yr[2:] if len(yr) == 4 else yr)
    return "", "", ""


def _draw_box(c, x, y, w, h, line=LINE):
    c.setLineWidth(line)
    c.setStrokeColor(black)
    c.rect(x, y, w, h, fill=0, stroke=1)


def _draw_field(c, x, y, w, h, label, value, *, label_size=6, value_size=10):
    """A boxed field: thick black border, value top-left bold, label inside bottom-left italic."""
    _draw_box(c, x, y, w, h)
    if value:
        c.setFont("Helvetica-Bold", value_size)
        c.setFillColor(black)
        c.drawString(x + 4, y + h - value_size - 3, str(value).upper()[: int(w / (value_size * 0.55))])
    c.setFont("Helvetica-Oblique", label_size)
    c.setFillColor(black)
    c.drawString(x + 3, y + 2, label)


def _draw_date_boxes(c, x, y, w_total, h, value, *, caption=""):
    """Three side-by-side cells (GG | MM | AA). Optional caption sits at the
    bottom-left INSIDE the row (so it never collides with the row below)."""
    cell_w = w_total / 3.0
    gg, mm, aa = _split_date(value)
    for i, (val, lbl) in enumerate([(gg, "GG"), (mm, "MM"), (aa, "AA")]):
        _draw_box(c, x + i * cell_w, y, cell_w, h, line=LINE)
        c.setFont("Helvetica", 5)
        c.setFillColor(black)
        c.drawString(x + i * cell_w + 2, y + h - 7, lbl)
        if val:
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x + i * cell_w + cell_w / 2.0, y + h / 2.0 - 4, val)
    if caption:
        c.setFont("Helvetica-Oblique", 6)
        c.drawString(x + 2, y + 2, caption)


def _draw_checkbox(c, x, y, size=9, checked=False):
    _draw_box(c, x, y, size, size, line=LINE)
    if checked:
        c.setLineWidth(1.4)
        c.line(x, y, x + size, y + size)
        c.line(x + size, y, x, y + size)


def _draw_vtag(c, x, y, h, text):
    """Black filled vertical tag with rotated white text (e.g. 'DICHIARANTE')."""
    c.setFillColor(black)
    c.rect(x, y, TAG_W, h, fill=1, stroke=0)
    c.saveState()
    c.translate(x + TAG_W / 2.0 + 3, y + h / 2.0)
    c.rotate(90)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.setFillColor(black)


def _draw_label_row(c, x, y, w, text, size=8):
    c.setFont("Helvetica", size)
    c.setFillColor(black)
    c.drawString(x, y, text)


# =====================================================================
def generate_hospitality_pdf(data: dict) -> BytesIO:
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=A4)
    c.setLineWidth(LINE)
    c.setStrokeColor(black)
    c.setFillColor(black)

    # ===== TITLE BAR (black bar, white text) =====
    bar_h = 36
    bar_y = PAGE_H - 28 - bar_h
    c.setFillColor(black)
    c.rect(LEFT, bar_y, RIGHT - LEFT, bar_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString((LEFT + RIGHT) / 2.0, bar_y + 22, "COMUNICAZIONE DI OSPITALITÀ")
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString((LEFT + RIGHT) / 2.0, bar_y + 11, "IN FAVORE DI CITTADINO EXTRACOMUNITARIO")
    c.setFont("Helvetica", 7.5)
    c.drawCentredString((LEFT + RIGHT) / 2.0, bar_y + 2, "(ARTICOLO 7 DEL DECRETO LEGISLATIVO 25 LUGLIO 1998 NR. 286)")
    c.setFillColor(black)

    # ===== "Il sottoscritto" =====
    y_cursor = bar_y - 14
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT, y_cursor, "Il sottoscritto")
    y_cursor -= 4

    # ===== DICHIARANTE block =====
    row_h = 28
    host_h = row_h * 3
    host_top = y_cursor
    host_bottom = host_top - host_h
    _draw_vtag(c, LEFT, host_bottom, host_h, "DICHIARANTE")

    # Row 1: Cognome | Nome (each half of inner width)
    half_w = INNER_W / 2.0
    r1_y = host_top - row_h
    _draw_field(c, INNER_LEFT, r1_y, half_w, row_h, "(Cognome)", data.get("host_surname", ""))
    _draw_field(c, INNER_LEFT + half_w, r1_y, half_w, row_h, "(Nome)", data.get("host_name", ""))

    # Row 2: GG MM AA | Comune di nascita | Provincia
    r2_y = r1_y - row_h
    dob_w = 75
    com_w = 230
    prov_w = INNER_W - dob_w - com_w
    _draw_date_boxes(c, INNER_LEFT, r2_y, dob_w, row_h, data.get("host_dob", ""), caption="(Data di nascita)")
    _draw_field(c, INNER_LEFT + dob_w, r2_y, com_w, row_h, "(Comune di nascita)", data.get("host_birth_place", ""))
    _draw_field(c, INNER_LEFT + dob_w + com_w, r2_y, prov_w, row_h, "(Provincia o nazione estera)", data.get("host_province", ""))

    # Row 3: Residenza (full inner width)
    r3_y = r2_y - row_h
    _draw_field(c, INNER_LEFT, r3_y, INNER_W, row_h,
                "(Residenza - Comune, provincia, via o piazza, nr. civico)",
                data.get("host_residence", ""))

    y_cursor = host_bottom - 16

    # ===== Duration row =====
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT, y_cursor, "ai sensi dell'art. 7 del D.lvo nr. 286/98,")
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(LEFT + 168, y_cursor, "DICHIARA CHE DAL")

    dur_y = y_cursor - 22
    dur_box_w = 75
    dur_box_h = 18
    _draw_date_boxes(c, LEFT + 270, dur_y, dur_box_w, dur_box_h, data.get("check_in_date", ""))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(LEFT + 270 + dur_box_w + 6, dur_y + 6, "E FINO AL")
    _draw_date_boxes(c, LEFT + 270 + dur_box_w + 50, dur_y, dur_box_w, dur_box_h, data.get("check_out_date", ""))

    indef_y = dur_y - 16
    is_indef = not data.get("check_out_date")
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(LEFT + 270, indef_y, "oppure")
    _draw_checkbox(c, LEFT + 305, indef_y - 2, size=10, checked=is_indef)
    c.drawString(LEFT + 320, indef_y, "A TEMPO INDETERMINATO")

    y_cursor = indef_y - 18

    # ===== Two hosting type checkbox rows =====
    hosting = (data.get("hosting_type") or "alloggio").lower()
    is_alloggio = hosting != "cessione"

    _draw_checkbox(c, LEFT, y_cursor - 2, size=10, checked=is_alloggio)
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT + 16, y_cursor, "ha fornito ")
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(LEFT + 56, y_cursor, "alloggio / ospitalità")
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT + 145, y_cursor, "al Signor / alla Signora:")
    y_cursor -= 14

    _draw_checkbox(c, LEFT, y_cursor - 2, size=10, checked=not is_alloggio)
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT + 16, y_cursor, "ha ceduto la ")
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(LEFT + 65, y_cursor, "proprietà o il godimento di beni immobili,")
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT + 240, y_cursor, "rustici o urbani al Signor / alla Signora:")
    y_cursor -= 8

    # ===== CITTADINO EXTRACOMUNITARIO block =====
    guest_h = row_h * 5
    guest_top = y_cursor
    guest_bottom = guest_top - guest_h
    _draw_vtag(c, LEFT, guest_bottom, guest_h, "CITTADINO EXTRACOMUNITARIO")

    # Row 1: Cognome | Nome
    g1_y = guest_top - row_h
    _draw_field(c, INNER_LEFT, g1_y, half_w, row_h, "(Cognome)", data.get("guest_surname", ""))
    _draw_field(c, INNER_LEFT + half_w, g1_y, half_w, row_h, "(Nome)", data.get("guest_name", ""))

    # Row 2: DOB | Comune nascita | Provincia/Nazione
    g2_y = g1_y - row_h
    _draw_date_boxes(c, INNER_LEFT, g2_y, dob_w, row_h, data.get("guest_dob", ""), caption="(Data di nascita)")
    _draw_field(c, INNER_LEFT + dob_w, g2_y, com_w, row_h, "(Comune di nascita)", data.get("guest_birth_place", ""))
    _draw_field(c, INNER_LEFT + dob_w + com_w, g2_y, prov_w, row_h, "(Provincia o nazione estera)", data.get("guest_birth_nation", ""))

    # Row 3: Cittadinanza | Residenza
    g3_y = g2_y - row_h
    cit_w = INNER_W * 0.38
    _draw_field(c, INNER_LEFT, g3_y, cit_w, row_h, "(Cittadinanza)", data.get("guest_citizenship", ""))
    _draw_field(c, INNER_LEFT + cit_w, g3_y, INNER_W - cit_w, row_h,
                "(Residenza - Comune, provincia, via o piazza, nr. civico)",
                data.get("guest_residence", ""))

    # Row 4: Tipo doc | Nr | Data di rilascio
    g4_y = g3_y - row_h
    tipo_w = INNER_W * 0.32
    nr_w = INNER_W * 0.36
    rel_w = INNER_W - tipo_w - nr_w
    _draw_field(c, INNER_LEFT, g4_y, tipo_w, row_h, "(Tipo documento)", data.get("doc_type", "PASSAPORTO") or "PASSAPORTO")
    _draw_field(c, INNER_LEFT + tipo_w, g4_y, nr_w, row_h, "(Nr. documento)", data.get("passport_number", ""))
    _draw_date_boxes(c, INNER_LEFT + tipo_w + nr_w, g4_y, rel_w, row_h, data.get("doc_issue_date", ""), caption="(Data di rilascio)")

    # Row 5: Autorità (full)
    g5_y = g4_y - row_h
    _draw_field(c, INNER_LEFT, g5_y, INNER_W, row_h,
                "(Autorità che ha rilasciato il documento)",
                data.get("doc_authority", ""))

    y_cursor = guest_bottom - 16

    # ===== Property header =====
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT, y_cursor,
                 "La presente dichiarazione viene resa in qualità di proprietario / intestatario dell'immobile sito in:")
    y_cursor -= 6

    # Row P1: Comune (large) | Provincia (small)
    p1_y = y_cursor - row_h
    com_main_w = INNER_W * 0.72
    _draw_field(c, INNER_LEFT, p1_y, com_main_w, row_h, "(Comune)", data.get("property_comune", ""))
    _draw_field(c, INNER_LEFT + com_main_w, p1_y, INNER_W - com_main_w, row_h, "(Provincia)", data.get("property_provincia", ""))

    # Row P2: Via | Numero | Interno | Piano
    p2_y = p1_y - row_h
    via_w = INNER_W * 0.55
    num_w = INNER_W * 0.15
    int_w = INNER_W * 0.15
    pia_w = INNER_W - via_w - num_w - int_w
    _draw_field(c, INNER_LEFT, p2_y, via_w, row_h, "(Via o piazza)", data.get("property_address", ""))
    _draw_field(c, INNER_LEFT + via_w, p2_y, num_w, row_h, "(Numero)", data.get("property_number", ""))
    _draw_field(c, INNER_LEFT + via_w + num_w, p2_y, int_w, row_h, "(Interno)", data.get("property_interno", ""))
    _draw_field(c, INNER_LEFT + via_w + num_w + int_w, p2_y, pia_w, row_h, "(Piano)", data.get("property_piano", ""))

    # Property block left tag (empty — no special tag, just close the rectangle)
    prop_h = row_h * 2
    _draw_box(c, LEFT, p2_y, TAG_W, prop_h)

    y_cursor = p2_y - 24

    # ===== Signature row =====
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    luogo = (data.get("property_comune", "") or
             (data.get("host_residence", "").split(",")[0] if data.get("host_residence") else ""))
    c.setFont("Helvetica", 8.5)
    c.drawString(LEFT, y_cursor, f"Luogo e data: {luogo.upper()}, {today}")
    # Signature line
    sig_x_start = LEFT + INNER_W * 0.55
    c.setLineWidth(LINE)
    c.line(sig_x_start, y_cursor - 4, RIGHT, y_cursor - 4)
    c.setFont("Helvetica-Oblique", 7)
    c.drawCentredString((sig_x_start + RIGHT) / 2.0, y_cursor - 14, "(firma del dichiarante)")

    y_cursor -= 28

    # ===== Separator + ALLEGATI =====
    c.setLineWidth(0.7)
    c.line(LEFT, y_cursor, RIGHT, y_cursor)
    y_cursor -= 10

    c.setFont("Helvetica-Bold", 7)
    c.drawString(LEFT, y_cursor, "ALLEGATI:")
    c.setFont("Helvetica", 6.5)
    allegati = [
        "• COPIA DI UN DOCUMENTO DEL DICHIARANTE",
        ("• COPIA DI UN DOCUMENTO DEL CESSIONARIO (COPIA DEL PERMESSO DI SOGGIORNO IN CORSO DI VALIDITÀ "
         "O COPIA DEL PASSAPORTO PAGINA DEI DATI ANAGRAFICI E DEL VISTO D'INGRESSO UNITAMENTE A FOTOCOPIA "
         "RICEVUTA ASSICURATA DELLE POSTE)"),
        ("• COPIA DELLA DOCUMENTAZIONE COMPROVANTE LA PROPRIETÀ O IL TITOLO DI GODIMENTO DELL'IMMOBILE "
         "(ATTO DI PROPRIETÀ, CONTRATTO DI LOCAZIONE, ECC.)"),
        ("• IL MODULO DEVE ESSERE SPEDITO CON RACCOMANDATA A/R IN DUE COPIE CON FIRMA IN ORIGINALE "
         "(TRATTENERE UNA TERZA COPIA)"),
    ]
    for line in allegati:
        # Wrap manually at ~110 chars per line at 6.5pt
        wrapped = _wrap(line, 130)
        for w_line in wrapped:
            y_cursor -= 8
            c.drawString(LEFT + 12 if not w_line.startswith("•") else LEFT, y_cursor, w_line)
    y_cursor -= 4

    # Separator
    c.setLineWidth(0.7)
    c.line(LEFT, y_cursor, RIGHT, y_cursor)
    y_cursor -= 9

    # ===== ARTICOLO 7 =====
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(LEFT, y_cursor, "ARTICOLO 7 DEL DECRETO LEGISLATIVO 25 LUGLIO 1998 NR. 286:")
    y_cursor -= 9
    c.setFont("Helvetica", 7)
    article = (
        "«Chiunque, a qualsiasi titolo, dà alloggio ovvero ospita uno straniero o apolide, anche se parente "
        "o affine, o lo assume per qualsiasi causa alle proprie dipendenze ovvero cede allo stesso la "
        "proprietà o il godimento di beni immobili, rustici o urbani posti sul territorio dello Stato, è "
        "tenuto a darne comunicazione scritta, entro 48 ore, all'Autorità locale di pubblica sicurezza. "
        "Le violazioni delle disposizioni di cui al presente articolo sono soggette alla sanzione "
        "amministrativa del pagamento di una somma da 160 a 1.100 €.»"
    )
    for w_line in _wrap(article, 130):
        c.drawString(LEFT, y_cursor, w_line)
        y_cursor -= 9

    c.showPage()
    c.save()
    out.seek(0)
    return out


def _wrap(text: str, max_chars: int) -> list[str]:
    """Wrap text to lines of approximately max_chars width (word-aware)."""
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + 1 + len(w) <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
