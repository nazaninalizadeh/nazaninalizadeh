"""
Invoice PDF Generator — CONSIMMOBILIARI
Two templates, both drawn with ReportLab canvas primitives (no table abstractions,
no colored backgrounds) to match the official artifacts provided by the client:

1. `generate_fattura_pdf(data)`      — Standard "Fattura" (replica of COEB example)
2. `generate_preavviso_pdf(data)`    — "Preavviso di fatturazione" (replica of ELEISON example)

Both return a BytesIO buffer positioned at 0.
"""

from io import BytesIO
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


# --- Fixed issuer info (CONSIMMOBILIARI) -----------------------------------
ISSUER_NAME = "CONSIMMOBILIARI SAS DI SERRANO' ANTONINO & C."
ISSUER_NAME_SHORT = "CONSIMMOBILIARI S.A.S."
ISSUER_ADDRESS = "VIA VIGONOVESE 114 - 35127 - PADOVA (PD)"
ISSUER_ADDRESS_SHORT = "Via Vigonovese, 114 - 35127 Padova"
ISSUER_PIVA = "05093180288"
ISSUER_CF = "05093180288"
ISSUER_PHONE = "Tel: 049 8702639 / 393 9054080"
BANK_NAME = "Banca Monte dei Paschi di Siena"
BANK_IBAN = "IT14P0103012108000001107662"


# --- Helpers ---------------------------------------------------------------
def _fmt_eur(amount: float) -> str:
    """Italian number formatting: 1.342,00"""
    try:
        v = float(amount)
    except (TypeError, ValueError):
        v = 0.0
    # 1234567.89 -> "1.234.567,89"
    neg = v < 0
    v = abs(v)
    s = f"{v:,.2f}"  # 1,234,567.89
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    if neg:
        s = "-" + s
    return f"\u20ac {s}"


def _fmt_date_it(iso_or_date: str) -> str:
    """Return DD/MM/YYYY from an ISO date like YYYY-MM-DD or already DD/MM/YYYY."""
    if not iso_or_date:
        return ""
    s = str(iso_or_date)[:10]
    if "/" in s:
        return s
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return s


# =============================================================================
# 1) FATTURA (Standard Invoice) — Replica of COEB-COSTRUZIONI example
# =============================================================================
def generate_fattura_pdf(data: dict) -> BytesIO:
    """
    data keys (all optional with sensible defaults):
      invoice_number     : "20/2026"
      invoice_date       : "17/04/2026" or ISO "2026-04-17"
      recipient_name     : "COEB COSTRUZIONI S.R.L"
      recipient_address  : "VIA ANTONIANA 218/A"
      recipient_city     : "35011 CAMPODARSEGO (PD)"
      recipient_piva     : ""  (optional)
      recipient_cf       : ""  (optional)
      line_description   : "Ricerca inquilino per vostro appartamento ..."
      line_amount        : 1100.00     (imponibile, senza IVA)
      vat_rate           : 22          (percentuale)
      due_date           : "17/04/2026"
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    LEFT = 20 * mm
    RIGHT = W - 20 * mm

    # ---- Header: issuer (top-right block) --------------------------------
    y = H - 22 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(RIGHT, y, ISSUER_NAME)
    y -= 11
    c.setFont("Helvetica", 8)
    c.drawRightString(RIGHT, y, ISSUER_ADDRESS)
    y -= 10
    c.drawRightString(RIGHT, y, f"P.iva {ISSUER_PIVA} - C.F. {ISSUER_CF}")

    # ---- Invoice number + date (left side, top) --------------------------
    y_fnum = H - 22 * mm
    c.setFont("Helvetica-Bold", 12)
    inv_num = str(data.get("invoice_number", ""))
    inv_date = _fmt_date_it(data.get("invoice_date") or datetime.now().strftime("%Y-%m-%d"))
    c.drawString(LEFT, y_fnum, f"FATTURA nr.  {inv_num}    del  {inv_date}")

    # ---- Horizontal separator line below header --------------------------
    sep_y = H - 50 * mm
    c.setLineWidth(0.5)
    c.line(LEFT, sep_y, RIGHT, sep_y)

    # ---- Destinatario block (right side, just below separator) -----------
    y = sep_y - 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT, y, "DESTINATARIO")
    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT, y, str(data.get("recipient_name", "")).upper())
    y -= 12
    c.setFont("Helvetica", 9)
    if data.get("recipient_address"):
        c.drawString(LEFT, y, str(data["recipient_address"]).upper())
        y -= 11
    if data.get("recipient_city"):
        c.drawString(LEFT, y, str(data["recipient_city"]).upper())
        y -= 11
    if data.get("recipient_piva"):
        c.drawString(LEFT, y, f"P.IVA {data['recipient_piva']}")
        y -= 11
    if data.get("recipient_cf"):
        c.drawString(LEFT, y, f"C.F. {data['recipient_cf']}")
        y -= 11

    # ---- Item table header ------------------------------------------------
    table_top = sep_y - 85
    c.setLineWidth(0.5)
    c.line(LEFT, table_top, RIGHT, table_top)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT + 4, table_top - 14, "DESCRIZIONE")
    c.drawRightString(RIGHT - 4, table_top - 14, "IMPORTO")
    c.line(LEFT, table_top - 20, RIGHT, table_top - 20)

    # ---- Line item --------------------------------------------------------
    line_y = table_top - 40
    c.setFont("Helvetica", 9)
    desc = str(data.get("line_description", ""))
    # wrap long description
    max_chars = 80
    parts = []
    while len(desc) > max_chars:
        cut = desc.rfind(" ", 0, max_chars)
        if cut <= 0:
            cut = max_chars
        parts.append(desc[:cut])
        desc = desc[cut:].lstrip()
    parts.append(desc)
    for i, p in enumerate(parts):
        c.drawString(LEFT + 4, line_y - i * 12, p)

    line_amount = float(data.get("line_amount", 0) or 0)
    c.setFont("Helvetica", 10)
    c.drawRightString(RIGHT - 4, line_y, _fmt_eur(line_amount))

    # closing line under item
    close_y = line_y - 12 * len(parts) - 8
    c.setLineWidth(0.3)
    c.line(LEFT, close_y, RIGHT, close_y)

    # ---- Riepilogo IVA (left side) ---------------------------------------
    vat_rate = float(data.get("vat_rate", 22) or 0)
    imponibile = line_amount
    imposte = round(imponibile * vat_rate / 100.0, 2)
    totale = round(imponibile + imposte, 2)

    ry = close_y - 30
    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT, ry, "RIEPILOGO IVA")
    ry -= 14
    c.setFont("Helvetica-Bold", 8)
    col1 = LEFT
    col2 = LEFT + 60
    col3 = LEFT + 130
    c.drawString(col1, ry, "ALIQUOTA")
    c.drawString(col2, ry, "IMPONIBILE")
    c.drawString(col3, ry, "IMPOSTE")
    ry -= 4
    c.line(LEFT, ry, LEFT + 200, ry)
    ry -= 12
    c.setFont("Helvetica", 9)
    c.drawString(col1, ry, f"{int(vat_rate)}%")
    c.drawString(col2, ry, _fmt_eur(imponibile))
    c.drawString(col3, ry, _fmt_eur(imposte))

    # ---- Totals box (right side) -----------------------------------------
    box_w = 180
    box_h = 85
    box_x = RIGHT - box_w
    box_y = close_y - 30 - box_h
    c.setLineWidth(0.5)
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

    inner_pad = 10
    ty = box_y + box_h - inner_pad - 4
    c.setFont("Helvetica-Bold", 9)
    c.drawString(box_x + inner_pad, ty, "Imponibile")
    c.setFont("Helvetica", 10)
    c.drawRightString(box_x + box_w - inner_pad, ty, _fmt_eur(imponibile))

    ty -= 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(box_x + inner_pad, ty, "Totale IVA")
    c.setFont("Helvetica", 10)
    c.drawRightString(box_x + box_w - inner_pad, ty, _fmt_eur(imposte))

    ty -= 5
    c.line(box_x + inner_pad, ty, box_x + box_w - inner_pad, ty)

    ty -= 22
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(box_x + box_w - inner_pad, ty, _fmt_eur(totale))

    # ---- Payment footer --------------------------------------------------
    foot_y = 70 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT, foot_y, "MODALITA' DI PAGAMENTO")
    c.setFont("Helvetica", 9)
    c.drawString(LEFT, foot_y - 14, "BONIFICO BANCARIO")
    c.drawString(LEFT, foot_y - 28, f"IBAN: {BANK_IBAN}")
    c.drawString(LEFT, foot_y - 42, BANK_NAME)

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(RIGHT, foot_y, "SCADENZE")
    due = _fmt_date_it(data.get("due_date") or data.get("invoice_date") or "")
    c.setFont("Helvetica", 9)
    c.drawRightString(RIGHT, foot_y - 14, f"{due}: {_fmt_eur(totale)}")

    # bottom disclaimer
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(W / 2, 12 * mm,
                        "Documento generato elettronicamente da CONSIMMOBILIARI S.A.S.")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


# =============================================================================
# 2) PREAVVISO DI FATTURAZIONE — Replica of ELEISON example
# =============================================================================
def generate_preavviso_pdf(data: dict) -> BytesIO:
    """
    data keys:
      causale_date       : "29/10/25" or ISO
      recipient_name     : "ELEISON Societa' Cooperativa Sociale"
      recipient_address  : "Via Giorgio Pulle' 15/17 Padova"
      recipient_cf_piva  : "05028740289"
      body_text          : "Ricerca appartamento in locazione situato a Padova Via Mozart"
      imponibile         : 1300.00
      vat_rate           : 22     (use 0 for exempt items)
      rimborso_label     : "Rimborso spese vostra quota registrazione contratto"
      rimborso_amount    : 186.00
      rimborso_note      : "(Imposta di bollo non presente in quanto cooperativa onlus)"
      rimborso_tax_note  : "(esente iva art 15)"
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    LEFT = 20 * mm
    RIGHT = W - 20 * mm

    # ---- Issuer (top-left block) -----------------------------------------
    y = H - 25 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(LEFT, y, ISSUER_NAME_SHORT)
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(LEFT, y, ISSUER_ADDRESS_SHORT)
    y -= 13
    c.drawString(LEFT, y, f"Partita IVA {ISSUER_PIVA}    {ISSUER_PHONE}")

    # ---- Recipient (right-side block) ------------------------------------
    ry = H - 25 * mm
    x_rec = LEFT + 95 * mm
    c.setFont("Helvetica", 10)
    c.drawString(x_rec, ry, "Spett.le")
    ry -= 14
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_rec, ry, str(data.get("recipient_name", "")))
    ry -= 14
    c.setFont("Helvetica", 10)
    if data.get("recipient_address"):
        c.drawString(x_rec, ry, str(data["recipient_address"]))
        ry -= 13
    if data.get("recipient_cf_piva"):
        c.drawString(x_rec, ry, f"C.F. P.IVA {data['recipient_cf_piva']}")
        ry -= 13

    # ---- Horizontal separator --------------------------------------------
    sep_y = H - 68 * mm
    c.setLineWidth(0.5)
    c.line(LEFT, sep_y, RIGHT, sep_y)

    # ---- CAUSALE line ----------------------------------------------------
    caus_date = _fmt_date_it(data.get("causale_date") or datetime.now().strftime("%Y-%m-%d"))
    # the template uses DD/MM/YY (2 digits) — we mimic it if possible
    try:
        d = datetime.strptime(caus_date, "%d/%m/%Y")
        caus_date_short = d.strftime("%d/%m/%y")
    except ValueError:
        caus_date_short = caus_date

    c.setFont("Helvetica-Bold", 13)
    c.drawString(LEFT, sep_y - 18, f"CAUSALE : preavviso fatturazione del {caus_date_short}")

    # ---- Body text --------------------------------------------------------
    body = str(data.get("body_text", ""))
    c.setFont("Helvetica", 11)
    by = sep_y - 45
    # wrap
    max_chars = 90
    while body:
        if len(body) <= max_chars:
            c.drawString(LEFT, by, body)
            by -= 14
            break
        cut = body.rfind(" ", 0, max_chars)
        if cut <= 0:
            cut = max_chars
        c.drawString(LEFT, by, body[:cut])
        body = body[cut:].lstrip()
        by -= 14

    by -= 15

    # ---- Line items -------------------------------------------------------
    imponibile = float(data.get("imponibile", 0) or 0)
    vat_rate = float(data.get("vat_rate", 22) or 0)
    imposte = round(imponibile * vat_rate / 100.0, 2)
    rimb = float(data.get("rimborso_amount", 0) or 0)
    rimb_label = str(data.get("rimborso_label", "") or "")
    rimb_note = str(data.get("rimborso_note", "") or "")
    rimb_tax_note = str(data.get("rimborso_tax_note", "") or "")
    totale = round(imponibile + imposte + rimb, 2)

    c.setFont("Helvetica", 11)
    # First item: imponibile line
    c.drawString(LEFT, by, f"Imponibile {int(vat_rate)}%" if vat_rate else "Imponibile")
    c.drawRightString(RIGHT, by, _fmt_eur(imponibile))
    by -= 16

    if vat_rate:
        c.drawString(LEFT, by, f"Iva {int(vat_rate)}%")
        c.drawRightString(RIGHT, by, _fmt_eur(imposte))
        by -= 16

    if rimb > 0 or rimb_label:
        c.drawString(LEFT, by, rimb_label or "Rimborso spese")
        amt_str = _fmt_eur(rimb)
        if rimb_tax_note:
            amt_str = f"{amt_str}  {rimb_tax_note}"
        c.drawRightString(RIGHT, by, amt_str)
        by -= 14
        if rimb_note:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(LEFT, by, rimb_note)
            by -= 14
            c.setFont("Helvetica", 11)

    by -= 6
    c.setLineWidth(0.5)
    c.line(LEFT, by, RIGHT, by)
    by -= 22

    # ---- TOTALE FATTURA --------------------------------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(LEFT, by, "TOTALE FATTURA")
    c.drawRightString(RIGHT, by, _fmt_eur(totale))

    # ---- Payment footer --------------------------------------------------
    foot_y = 45 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(LEFT, foot_y, "BONIFICO BANCARIO PRESSO")
    c.setFont("Helvetica", 11)
    c.drawString(LEFT, foot_y - 16, BANK_NAME)
    c.drawString(LEFT, foot_y - 32, f"Iban {BANK_IBAN}")

    # small company caption bottom-right
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(RIGHT, 22 * mm, ISSUER_NAME_SHORT)
    c.setFont("Helvetica", 8)
    c.drawRightString(RIGHT, 22 * mm - 11, "Via Vigonovese 114 - Padova")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
