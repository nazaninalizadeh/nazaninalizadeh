"""One-time prep utility: render the JALLAB hospitality template to PNG and
white-out the pre-filled handwriting zones, leaving only the form structure.
The output ``hospitality_template_clean.png`` is used by hospitality_pdf.py
as a background. Only the printed form (title bar, labels, lines, ALLEGATI,
ARTICOLO 7) remains visible — handwriting is gone.

Run manually whenever the template changes:
    python -m backend.scripts.prepare_hospitality_template
or just `python /app/backend/scripts/prepare_hospitality_template.py`.
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

TEMPLATES = Path("/app/backend/templates")
SRC_PDF = TEMPLATES / "hospitality_template.pdf"
RAW_PREFIX = TEMPLATES / "hospitality_raw"
RAW_PNG = TEMPLATES / "hospitality_raw-1.png"
CLEAN_PNG = TEMPLATES / "hospitality_template_clean.png"

PAGE_W_PT = 603.6
PAGE_H_PT = 846.72
DPI = 200
PT_TO_PX = DPI / 72.0  # 200/72 ≈ 2.778

# Whitelisted handwriting zones in PDF point coords. Format: (x, y_top, w, h)
# with y_top = upper edge of the rectangle (PDF origin at bottom-left).
# Zones are calibrated to NOT clip the form's own pre-printed labels.
ZONES_PT = [
    # ===== HOST =====
    (138, 778, 470, 43),    # host Cognome + Nome value row (above (Cognome) label at y≈732)
    (95,  725, 485, 30),    # host DOB GG-MM-AA + Comune di nascita + Provincia/nazione (above labels at y≈693)
    (78,  688, 480, 28),    # host Residenza row (above label at y≈658)
    # ===== Duration =====
    (380, 660, 200, 28),    # check-in date boxes
    (380, 632, 200, 28),    # check-out date boxes
    # ===== Original checkboxes (TEMPO INDETERMINATO + alloggio + cessione X-marks) =====
    (655, 622, 28, 35),     # JALLAB X — covers leftover X near "E FINO AL" line too
    (66,  582, 24, 22),     # JALLAB X on "ha fornito alloggio"
    (66,  559, 24, 22),     # JALLAB box on "ha ceduto"
    # ===== GUEST =====
    (138, 540, 470, 30),    # guest Cognome + Nome value row (above label at y≈509)
    (95,  503, 485, 28),    # guest DOB + Comune nascita + Nazione (above labels at y≈474)
    (78,  470, 220, 30),    # guest Cittadinanza
    (288, 470, 290, 30),    # guest Residenza
    (78,  434, 200, 22),    # guest Tipo documento
    (260, 434, 110, 22),    # guest Numero documento
    (376, 434, 200, 22),    # guest Data di rilascio
    (78,  405, 500, 28),    # guest Autorità che ha rilasciato
    # ===== PROPERTY =====
    (78,  338, 500, 28),    # property Comune + Provincia (above label at y≈309)
    (78,  302, 500, 26),    # property Via + Numero + Interno + Piano (above labels at y≈274)
    # ===== Signature =====
    (78,  267, 350, 30),    # Luogo e data handwritten line
    (430, 260, 170, 38),    # Signature scribble area
]


def _rect_pt_to_px(x_pt, y_top_pt, w_pt, h_pt):
    """Translate a PDF rectangle (origin bottom-left) to a PIL bounding box."""
    x0 = int(x_pt * PT_TO_PX)
    x1 = int((x_pt + w_pt) * PT_TO_PX)
    y_top_im = int((PAGE_H_PT - y_top_pt) * PT_TO_PX)
    y_bot_im = int((PAGE_H_PT - (y_top_pt - h_pt)) * PT_TO_PX)
    return [x0, y_top_im, x1, y_bot_im]


def main():
    # Render template to PNG at 200 DPI
    subprocess.check_call([
        "pdftoppm", "-r", str(DPI), str(SRC_PDF), str(RAW_PREFIX),
        "-png", "-f", "1", "-l", "1",
    ])
    img = Image.open(RAW_PNG).convert("RGB")
    draw = ImageDraw.Draw(img)
    for r in ZONES_PT:
        draw.rectangle(_rect_pt_to_px(*r), fill="white")
    img.save(CLEAN_PNG, "PNG", optimize=True)
    print(f"Wrote {CLEAN_PNG} ({CLEAN_PNG.stat().st_size // 1024} KB)")
    if RAW_PNG.exists():
        RAW_PNG.unlink()


if __name__ == "__main__":
    main()
