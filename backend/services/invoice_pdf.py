"""
Invoice PDF Generator — CONSIMMOBILIARI

Pixel-by-pixel replicas of the official reference templates using ReportLab
canvas drawing primitives (drawString / drawRightString / line).
NO colored backgrounds, NO modern UI, NO HTML/CSS layout.

Two templates:
  1) generate_fattura_pdf(data)    — replica of "Fattura 20/2026" (COEB)
  2) generate_preavviso_pdf(data)  — replica of "Preavviso fatturazione" (ELEISON)
"""

from io import BytesIO
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


# ---- Fixed issuer info ----------------------------------------------------
ISSUER_NAME = "CONSIMMOBILIARI SAS DI SERRANO' ANTONINO & C."
ISSUER_NAME_LARGE = "CONSIMMOBILIARI S.A.S."
ISSUER_ADDR_FULL = "VIA VIGONOVESE 114 - 35127 - PADOVA (PD)"
ISSUER_ADDR_SHORT = "Via Vigonovese, 114  35127 Padova"
ISSUER_PIVA = "05093180288"
ISSUER_CF = "05093180288"
ISSUER_PHONE = "Tel: 049 8702639 /  393 9054080"
ISSUER_EMAIL = "consimmobiliarisas1@gmail.com"
BANK_NAME = "Banca Monte dei Paschi di Siena"
BANK_IBAN = "IT14P0103012108000001107662"


# ---- Helpers --------------------------------------------------------------
def _fmt_eur(amount: float, with_symbol: bool = True) -> str:
    """Italian number formatting: 1.342,00 (optionally with € prefix)."""
    try:
        v = float(amount)
    except (TypeError, ValueError):
        v = 0.0
    neg = v < 0
    v = abs(v)
    s = f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if neg:
        s = "-" + s
    return f"\u20ac {s}" if with_symbol else s


def _fmt_date_it(s: str) -> str:
    if not s:
        return ""
    s = str(s)[:10]
    if "/" in s:
        return s
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return s


def _short_invoice_no(raw: str, year: int) -> str:
    """Always return 'N/YYYY' — strip any UUID-style prefix."""
    if not raw:
        return f"1/{year}"
    raw = str(raw).strip().lstrip("INV-")
    # if already in N/YYYY format keep it
    if "/" in raw and raw.split("/")[1].isdigit():
        return raw
    # Take last segment of '-'-split that is purely digits
    parts = [p for p in raw.replace("-", " ").split() if p.isdigit()]
    if parts:
        last = parts[-1].lstrip("0") or "0"
        # Limit to 4 digits to avoid huge numbers
        last = last[-4:]
        return f"{last}/{year}"
    return f"1/{year}"


def _wrap(text: str, max_chars: int):
    """Naive word-wrap: returns list of lines."""
    out, line = [], ""
    for word in str(text or "").split():
        if len(line) + len(word) + 1 <= max_chars:
            line = (line + " " + word).strip()
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out or [""]


# ============================================================================
# 1) FATTURA — replica of COEB Costruzioni reference (Fattura nr. 20/2026)
# ============================================================================
def generate_fattura_pdf(data: dict) -> BytesIO:
    """
    Required keys (all optional with defaults):
      invoice_number    : "20/2026"  (or any string — sanitised to N/YYYY)
      invoice_date      : "17/04/2026" or ISO
      recipient_name    : "COEB COSTRUZIONI S.R.L"
      recipient_address : "VIA ANTONIANA 218/A"
      recipient_city    : "35011 CAMPODARSEGO (PD)"
      recipient_piva    : "04301600286"
      recipient_cf      : "04301600286"
      line_description  : "Ricerca inquilino per vostro appartamento ..."
      line_amount       : 1100.00     (imponibile)
      vat_rate          : 22
      due_date          : "17/04/2026"
      page_index        : "1 / 1"
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    LEFT = 18 * mm
    RIGHT = W - 18 * mm

    # ---------- 1) Top-right header (issuer) ----------
    y = H - 18 * mm
    c.setFont("Helvetica-Bold", 9.5)
    c.drawRightString(RIGHT, y, ISSUER_NAME)
    y -= 11
    c.setFont("Helvetica", 8.5)
    c.drawRightString(RIGHT, y, ISSUER_ADDR_FULL)
    y -= 11
    c.drawRightString(RIGHT, y, f"P.iva {ISSUER_PIVA} - C.F. {ISSUER_CF}")

    # ---------- 2) "FATTURA nr. X/YYYY del DD/MM/YYYY" (right-aligned, own row) ----------
    inv_date_str = _fmt_date_it(data.get("invoice_date") or datetime.now().strftime("%Y-%m-%d"))
    try:
        year = int(inv_date_str.split("/")[-1])
    except (ValueError, IndexError):
        year = datetime.now().year
    inv_no = _short_invoice_no(data.get("invoice_number"), year)

    y -= 22
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(RIGHT, y, f"FATTURA  nr. {inv_no}  del  {inv_date_str}")

    # ---------- 3) Horizontal separator ----------
    sep_y = y - 18
    c.setLineWidth(0.4)
    c.line(LEFT, sep_y, RIGHT, sep_y)

    # ---------- 4) Recipient block ----------
    # Left: small CF/PIVA of recipient (matches reference)
    rec_y = sep_y - 16
    c.setFont("Helvetica-Bold", 9)
    if data.get("recipient_piva"):
        c.drawString(LEFT, rec_y, "P.IVA")
        c.setFont("Helvetica", 9)
        c.drawString(LEFT + 35, rec_y, str(data["recipient_piva"]))
    if data.get("recipient_cf"):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(LEFT, rec_y - 12, "CF")
        c.setFont("Helvetica", 9)
        c.drawString(LEFT + 35, rec_y - 12, str(data["recipient_cf"]))

    # Right: DESTINATARIO block
    rcol_x = LEFT + 95 * mm
    c.setFont("Helvetica", 7.5)
    c.drawString(rcol_x, rec_y, "DESTINATARIO")
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(rcol_x, rec_y - 13, str(data.get("recipient_name", "") or "").upper())
    c.setFont("Helvetica", 9)
    rec_addr = str(data.get("recipient_address", "") or "").upper()
    rec_city = str(data.get("recipient_city", "") or "").upper()
    if rec_addr:
        c.drawString(rcol_x, rec_y - 25, rec_addr)
    if rec_city:
        c.drawString(rcol_x, rec_y - 36, rec_city)

    # ---------- 5) Item table ----------
    table_top = sep_y - 70
    c.setLineWidth(0.4)
    c.line(LEFT, table_top, RIGHT, table_top)
    c.setFont("Helvetica", 7.5)
    c.drawString(LEFT + 4, table_top - 11, "DESCRIZIONE")
    c.drawRightString(RIGHT - 4, table_top - 11, "IMPORTO")
    c.line(LEFT, table_top - 16, RIGHT, table_top - 16)

    # Item row (single line)
    line_amount = float(data.get("line_amount", 0) or 0)
    desc_lines = _wrap(data.get("line_description", ""), 95)
    row_h = 14 + (len(desc_lines) - 1) * 11
    row_top = table_top - 16
    row_bot = row_top - row_h
    # very light shading (mimic reference's faint row tint via thin dotted-ish look = single bg line)
    # but rules say "no colors" — so we keep it crisp lines only.
    c.setFont("Helvetica-Bold", 9)
    for i, ln in enumerate(desc_lines):
        c.drawString(LEFT + 4, row_top - 11 - i * 11, ln)
    c.setFont("Helvetica", 9.5)
    c.drawRightString(RIGHT - 4, row_top - 11, _fmt_eur(line_amount))
    c.line(LEFT, row_bot, RIGHT, row_bot)

    # ---------- 6) NOTE / legal disclaimer ----------
    note_y = row_bot - 16
    c.setFont("Helvetica", 7.5)
    c.drawString(LEFT, note_y, "NOTE")
    c.setFont("Helvetica", 9)
    c.drawString(LEFT, note_y - 12,
                 "Documento privo di valenza fiscale ai sensi dell'art. 21 Dpr 633/72. "
                 "L'originale e' disponibile all'indirizzo telematico da Lei fornito")
    c.drawString(LEFT, note_y - 23,
                 "oppure nella Sua area riservata dell'Agenzia delle Entrate.")

    # ---------- 7) Bottom block: MODALITÀ DI PAGAMENTO + SCADENZE ----------
    pay_top = 105 * mm
    c.line(LEFT, pay_top, RIGHT, pay_top)
    c.setFont("Helvetica", 7.5)
    c.drawString(LEFT, pay_top - 11, "MODALITA' DI PAGAMENTO")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT, pay_top - 24, "BONIFICO BANCARIO")
    c.setFont("Helvetica", 9)
    c.drawString(LEFT, pay_top - 36, f"IBAN: {BANK_IBAN}")

    sc_x = LEFT + 95 * mm
    c.setFont("Helvetica", 7.5)
    c.drawString(sc_x, pay_top - 11, "SCADENZE")
    c.setFont("Helvetica-Bold", 9)
    due = _fmt_date_it(data.get("due_date") or data.get("invoice_date") or "")
    vat_rate = float(data.get("vat_rate", 22) or 0)
    imponibile = line_amount
    imposte = round(imponibile * vat_rate / 100.0, 2)
    totale = round(imponibile + imposte, 2)
    c.drawString(sc_x, pay_top - 24, f"{due}: {_fmt_eur(totale)}")

    # ---------- 8) Separator above RIEPILOGO IVA ----------
    riep_top = pay_top - 50
    c.line(LEFT, riep_top, RIGHT, riep_top)

    # ---------- 9) RIEPILOGO IVA (left side, aligned columns) ----------
    c.setFont("Helvetica", 7.5)
    c.drawString(LEFT, riep_top - 11, "RIEPILOGO IVA")
    col_alq = LEFT
    col_imp = LEFT + 60 * mm
    col_imposte = LEFT + 78 * mm
    c.drawString(col_alq, riep_top - 22, "")  # spacer
    c.setFont("Helvetica", 7.5)
    c.drawRightString(col_imp + 22, riep_top - 22, "IMPONIBILE")
    c.drawRightString(col_imposte + 22, riep_top - 22, "IMPOSTE")
    c.setFont("Helvetica", 9.5)
    c.drawString(col_alq, riep_top - 35, f"{int(vat_rate)}%")
    c.drawRightString(col_imp + 22, riep_top - 35, _fmt_eur(imponibile, with_symbol=False))
    c.drawRightString(col_imposte + 22, riep_top - 35, _fmt_eur(imposte))

    # ---------- 10) TOTAL block (right side, no border) ----------
    tx_right = RIGHT
    ty = riep_top - 18
    c.setFont("Helvetica", 9)
    c.drawRightString(tx_right - 70, ty, "Imponibile")
    c.drawRightString(tx_right, ty, _fmt_eur(imponibile))
    ty -= 12
    c.drawRightString(tx_right - 70, ty, "Totale IVA")
    c.drawRightString(tx_right, ty, _fmt_eur(imposte))
    ty -= 26
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(tx_right, ty, _fmt_eur(totale))

    # ---------- 11) Footer line + tiny captions ----------
    foot_y = 12 * mm
    c.setLineWidth(0.3)
    c.line(LEFT, foot_y + 12, RIGHT, foot_y + 12)
    c.setFont("Helvetica", 7)
    page_idx = data.get("page_index", "1 / 1")
    c.drawString(LEFT, foot_y, f"Fattura nr. {inv_no} del {inv_date_str} - {page_idx}")
    c.drawRightString(RIGHT, foot_y, f"{ISSUER_NAME}  {ISSUER_EMAIL}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


# ============================================================================
# 2) PREAVVISO — replica of ELEISON Cooperativa Sociale reference
# ============================================================================
def generate_preavviso_pdf(data: dict) -> BytesIO:
    """
    Required keys:
      causale_date       : "29/10/25" or ISO
      recipient_name     : "ELEISON Società Cooperativa Sociale"
      recipient_address  : "Via Giorgio Pullè 15/17 Padova"
      recipient_cf_piva  : "05028740289"
      body_text          : "Ricerca appartamento in locazione situato a Padova Via Mozart"
      imponibile         : 1300.00
      vat_rate           : 22
      rimborso_label     : "Rimborso spese vostra quota registrazione contratto"
      rimborso_amount    : 186.00
      rimborso_note      : "(Imposta di bollo non presente in quanto cooperativa onlus)"
      rimborso_tax_note  : "(esente iva art 15)"
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    LEFT = 18 * mm
    RIGHT = W - 18 * mm

    # ---------- 1) Top decorative horizontal accent (faint, right-side) ----------
    c.setLineWidth(0.5)
    c.line(W * 0.45, H - 14 * mm, RIGHT, H - 14 * mm)

    # ---------- 2) Issuer block (left, with vertical decorative rule) ----------
    block_top = H - 22 * mm
    block_bottom = H - 60 * mm
    # vertical accent line on its left
    c.setLineWidth(0.6)
    c.line(LEFT, block_top, LEFT, block_bottom)

    c.setFont("Helvetica-Bold", 22)
    c.drawString(LEFT + 6 * mm, H - 30 * mm, ISSUER_NAME_LARGE)

    c.setFont("Helvetica-Oblique", 10.5)
    c.drawString(LEFT + 6 * mm, H - 41 * mm, ISSUER_ADDR_SHORT)
    c.drawString(LEFT + 6 * mm, H - 52 * mm,
                 f"Partita IVA {ISSUER_PIVA} {ISSUER_PHONE}")

    # ---------- 3) Recipient block (right, lower) ----------
    rcol_x = LEFT + 95 * mm
    ry = H - 70 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(rcol_x, ry, "Spett.le")
    ry -= 13
    c.setFont("Helvetica-Bold", 11)
    c.drawString(rcol_x, ry, str(data.get("recipient_name", "")))
    ry -= 13
    c.setFont("Helvetica", 10)
    if data.get("recipient_address"):
        c.drawString(rcol_x, ry, str(data["recipient_address"]))
        ry -= 13
    if data.get("recipient_cf_piva"):
        c.drawString(rcol_x, ry, f"C.F.  P.IVA {data['recipient_cf_piva']}")

    # ---------- 4) Horizontal separator ----------
    sep_y = H - 105 * mm
    c.setLineWidth(0.5)
    c.line(LEFT, sep_y, RIGHT, sep_y)

    # ---------- 5) CAUSALE row ----------
    caus_full = _fmt_date_it(data.get("causale_date") or datetime.now().strftime("%Y-%m-%d"))
    try:
        d = datetime.strptime(caus_full, "%d/%m/%Y")
        caus_short = d.strftime("%d/%m/%y")
    except ValueError:
        caus_short = caus_full
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, sep_y - 16, f"CAUSALE : preavviso fatturazione del {caus_short}")

    # ---------- 6) Body text ----------
    body = str(data.get("body_text", "") or "")
    c.setFont("Helvetica", 11)
    by = sep_y - 42
    for ln in _wrap(body, 95):
        c.drawString(LEFT, by, ln)
        by -= 14

    # ---------- 7) Items: imponibile (no label), iva 22%, rimborso ----------
    imponibile = float(data.get("imponibile", 0) or 0)
    vat_rate = float(data.get("vat_rate", 22) or 0)
    imposte = round(imponibile * vat_rate / 100.0, 2)
    rimb = float(data.get("rimborso_amount", 0) or 0)
    rimb_label = str(data.get("rimborso_label", "") or "")
    rimb_note = str(data.get("rimborso_note", "") or "")
    rimb_tax_note = str(data.get("rimborso_tax_note", "") or "")
    totale = round(imponibile + imposte + rimb, 2)

    by -= 16
    c.setFont("Helvetica", 11)
    c.drawRightString(RIGHT, by, _fmt_eur(imponibile))
    by -= 16

    if vat_rate:
        c.drawString(LEFT + 95 * mm, by, f"Iva {int(vat_rate)}%")
        c.drawRightString(RIGHT, by, _fmt_eur(imposte))
        by -= 30

    if rimb > 0 or rimb_label:
        c.drawString(LEFT, by, rimb_label or "Rimborso")
        amt_str = _fmt_eur(rimb)
        if rimb_tax_note:
            amt_str = f"{amt_str} {rimb_tax_note}"
        c.drawRightString(RIGHT, by, amt_str)
        by -= 14
        if rimb_note:
            c.setFont("Helvetica", 9)
            c.drawString(LEFT, by, rimb_note)
            by -= 14
            c.setFont("Helvetica", 11)

    # ---------- 8) Separator + TOTAL FATTURA ----------
    by -= 6
    c.setLineWidth(0.5)
    c.line(LEFT, by, RIGHT, by)
    by -= 18
    c.setFont("Helvetica-Bold", 13)
    c.drawString(LEFT, by, "TOTALE FATTURA")
    c.drawRightString(RIGHT, by, _fmt_eur(totale))

    # ---------- 9) Bank info (bottom-left) ----------
    foot_y = 55 * mm
    c.setFont("Helvetica", 11)
    c.drawString(LEFT, foot_y, "BONIFICO BANCARIO PRESSO")
    c.drawString(LEFT, foot_y - 14, BANK_NAME)
    c.drawString(LEFT, foot_y - 28, f"Iban {BANK_IBAN}")

    # ---------- 10) Bottom-right small caption ----------
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(RIGHT, 22 * mm, ISSUER_NAME_LARGE)
    c.setFont("Helvetica", 8)
    c.drawRightString(RIGHT, 22 * mm - 11, "Via Vigonovese 114 - Padova")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
