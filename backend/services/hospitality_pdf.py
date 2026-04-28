"""COMUNICAZIONE DI OSPITALITA' PDF generator.

Uses the official JALLAB Italian government form as a pre-cleaned background
image (handwriting white-out applied at /app/backend/templates/
hospitality_template_clean.png — see scripts/prepare_hospitality_template.py).
On top of that image we overlay the system data at exact field coordinates,
so the printed result looks like the official template filled in by hand.

DO NOT redesign this module. Only adjust coordinates if the template image
itself is regenerated.
"""

from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

from reportlab.pdfgen import canvas


TEMPLATE_PNG = Path(__file__).parent.parent / "templates" / "hospitality_template_clean.png"
PAGE_W = 603.6
PAGE_H = 846.72


def _split_date(d: str) -> tuple[str, str, str]:
    """Return (GG, MM, AA-2-digit). Accepts ISO 'YYYY-MM-DD' or 'DD/MM/YYYY'."""
    if not d:
        return "", "", ""
    s = d.strip()
    if "-" in s and len(s) >= 10:
        try:
            return s[8:10], s[5:7], s[2:4]
        except Exception:
            pass
    if "/" in s:
        p = s.split("/")
        if len(p) == 3:
            yr = p[2]
            return p[0], p[1], (yr[2:] if len(yr) == 4 else yr)
    return "", "", ""


def generate_hospitality_pdf(data: dict) -> BytesIO:
    """Render the JALLAB-format hospitality form filled with system data."""
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=(PAGE_W, PAGE_H))

    # Background: cleaned official template
    c.drawImage(str(TEMPLATE_PNG), 0, 0, width=PAGE_W, height=PAGE_H, mask="auto")

    def text(x: float, y: float, value, size: int = 11, font: str = "Helvetica-Bold"):
        s = "" if value is None else str(value)
        c.setFont(font, size)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y, s.upper())

    def date_boxes(x0: float, y: float, date: str, dx: float = 26.0):
        gg, mm, aa = _split_date(date)
        for i, val in enumerate([gg, mm, aa]):
            text(x0 + i * dx + 4, y, val, size=11)

    def cross(x: float, y: float, size: float = 10):
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1.6)
        c.line(x, y, x + size, y + size)
        c.line(x + size, y, x, y + size)

    # ============================================================
    # All Y values are in real PDF coordinates (origin bottom-left).
    # Calibrated against /templates/hospitality_template_clean.png.
    # ============================================================

    # ----- DICHIARANTE -----
    text(150, 760, data.get("host_surname", ""), size=12)
    text(355, 760, data.get("host_name", ""), size=12)

    date_boxes(98, 716, data.get("host_dob", ""))
    text(185, 716, data.get("host_birth_place", ""), size=11)
    text(425, 716, data.get("host_province", ""), size=11)

    text(85, 674, data.get("host_residence", ""), size=11)

    # ----- Duration -----
    date_boxes(385, 645, data.get("check_in_date", ""))
    date_boxes(385, 619, data.get("check_out_date", ""))

    # If no check_out_date set, mark "A TEMPO INDETERMINATO"
    is_indef = not data.get("check_out_date")
    if is_indef:
        cross(660, 595, size=10)

    # ----- Hosting type checkboxes (alloggio vs cessione) -----
    hosting = (data.get("hosting_type") or "alloggio").lower()
    is_alloggio = hosting != "cessione"
    if is_alloggio:
        cross(72, 572, size=10)
    else:
        cross(72, 549, size=10)

    # ----- CITTADINO EXTRACOMUNITARIO -----
    text(150, 526, data.get("guest_surname", ""), size=12)
    text(355, 526, data.get("guest_name", ""), size=12)

    date_boxes(98, 488, data.get("guest_dob", ""))
    text(185, 488, data.get("guest_birth_place", ""), size=11)
    text(425, 488, data.get("guest_birth_nation", ""), size=11)

    text(85, 455, data.get("guest_citizenship", ""), size=11)
    text(295, 455, data.get("guest_residence", ""), size=10)

    text(85, 422, data.get("doc_type", "PASSAPORTO") or "PASSAPORTO", size=11)
    text(270, 422, data.get("passport_number", ""), size=11)
    date_boxes(380, 422, data.get("doc_issue_date", ""))

    text(85, 392, data.get("doc_authority", ""), size=11)

    # ----- PROPERTY -----
    text(85, 325, data.get("property_comune", ""), size=11)
    text(475, 325, data.get("property_provincia", ""), size=11)

    text(85, 290, data.get("property_address", ""), size=11)
    text(295, 290, data.get("property_number", ""), size=11)
    text(365, 290, data.get("property_interno", ""), size=11)
    text(435, 290, data.get("property_piano", ""), size=11)

    # ----- Signature -----
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    luogo = (data.get("property_comune", "") or
             (data.get("host_residence", "").split(",")[0] if data.get("host_residence") else ""))
    text(85, 256, f"LUOGO E DATA: {luogo}, {today}", size=10)

    c.showPage()
    c.save()
    out.seek(0)
    return out
