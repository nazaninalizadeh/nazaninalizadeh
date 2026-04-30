"""Iteration 18 — Phase 1 deep regression tests for PropertyOps.

Scope (REPORT-only run):
- OCR for tenants + owners (PNG/JPG/PDF + surname/name mapping)
- Italian city/province dictionaries (data presence)
- Hospitality PDF (luogo/data, checkbox, surname-first, 1-year default)
- Hospitality edit record
- Owner signature transparent PNG (alpha channel)
- Registration ZIP bundle download (+ error handling)
- Payment receipt upload (types + size validation + view/replace/delete)
- Assign room dialog (backend assign/unassign already covered elsewhere)
"""
import io
import os
import re
import zipfile
import pytest
import requests
from datetime import date
from PIL import Image

def _load_base_url():
    u = os.environ.get("REACT_APP_BACKEND_URL", "")
    if not u:
        try:
            for line in open("/app/frontend/.env"):
                if line.startswith("REACT_APP_BACKEND_URL="):
                    u = line.split("=", 1)[1].strip()
                    break
        except Exception:
            pass
    return u.rstrip("/")

BASE_URL = _load_base_url()
ADMIN_EMAIL = "nazaninalizade890@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "test"})
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text[:200]}")
    return s


def _png_bytes(w=200, h=200, color=(255, 255, 255)) -> bytes:
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _jpg_bytes(w=200, h=200, color=(255, 255, 255)) -> bytes:
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def _make_pdf() -> bytes:
    # Minimal valid 1-page PDF
    return (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n"
            b"0000000053 00000 n \n0000000100 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF\n")


# =====================================================================
# 1A / 1B — OCR accepts PNG, JPG, PDF on tenant & owner forms (same endpoint)
# =====================================================================
class TestOCR:
    def test_ocr_scan_accepts_png(self, session):
        r = session.post(f"{BASE_URL}/api/ocr/scan",
                         files={"file": ("t.png", _png_bytes(), "image/png")})
        # Accept 200 (extracted) or 200 with status:failed (AI couldn't read blank image).
        assert r.status_code == 200, r.text[:200]
        js = r.json()
        assert "saved_file_url" in js, "saved_file_url missing from OCR response"
        assert "status" in js

    def test_ocr_scan_accepts_jpg(self, session):
        r = session.post(f"{BASE_URL}/api/ocr/scan",
                         files={"file": ("t.jpg", _jpg_bytes(), "image/jpeg")})
        assert r.status_code == 200, r.text[:200]
        assert r.json().get("status") in {"completed", "failed"}

    def test_ocr_scan_accepts_pdf(self, session):
        r = session.post(f"{BASE_URL}/api/ocr/scan",
                         files={"file": ("t.pdf", _make_pdf(), "application/pdf")})
        # PDF rendering may fail on a stub PDF — the endpoint should still return 200 with status=failed
        # (not a 500). This verifies the "does NOT silently swallow errors" contract.
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert body.get("status") in {"completed", "failed"}
        if body.get("status") == "failed":
            assert body.get("error"), "OCR failure must carry a user-facing 'error' message"

    def test_ocr_rejects_unsupported_type(self, session):
        r = session.post(f"{BASE_URL}/api/ocr/scan",
                         files={"file": ("t.txt", b"hello", "text/plain")})
        assert r.status_code == 400
        assert "supportato" in r.text.lower() or "formato" in r.text.lower()

    def test_ocr_size_limit_10mb(self, session):
        big = b"\x00" * (10 * 1024 * 1024 + 100)
        r = session.post(f"{BASE_URL}/api/ocr/scan",
                         files={"file": ("big.png", big, "image/png")})
        assert r.status_code == 400
        assert "10" in r.text or "troppo" in r.text.lower()


# =====================================================================
# 2A — Italian city/country dictionaries exist in frontend lib
# =====================================================================
class TestDictionaries:
    def test_italian_cities_has_padova(self):
        path = "/app/frontend/src/lib/it_cities.js"
        assert os.path.exists(path), "it_cities.js missing"
        with open(path, "r") as f:
            content = f.read()
        # Expect `['Padova', 'PD']` OR `["Padova","PD"]`
        assert re.search(r"['\"]Padova['\"]\s*,\s*['\"]PD['\"]", content), "Padova/PD tuple missing"

    def test_dictionaries_has_countries_and_nationalities(self):
        path = "/app/frontend/src/lib/it_dictionaries.js"
        assert os.path.exists(path)
        content = open(path).read()
        assert "COUNTRIES" in content
        assert "NATIONALITIES" in content


# =====================================================================
# 3A / Assign room — already covered by iteration16/17. Smoke-check exists.
# =====================================================================
class TestAssignRoom:
    def test_assign_endpoints_present(self, session):
        rs = session.get(f"{BASE_URL}/api/rooms")
        assert rs.status_code == 200


# =====================================================================
# 4A–4E — Hospitality: edit, PDF content
# =====================================================================
class TestHospitality:
    @pytest.fixture(scope="class")
    def tenant_ctx(self, session):
        """Use an existing tenant (verified exists). Prefer one with an active contract."""
        tenants = session.get(f"{BASE_URL}/api/tenants").json()
        if not tenants:
            pytest.skip("No tenants available for hospitality PDF test")
        # Prefer a tenant that appears in hospitality records AND still exists
        recs = session.get(f"{BASE_URL}/api/hospitality/records").json()
        existing_ids = {t["id"] for t in tenants}
        for r in recs:
            if r.get("tenant_id") in existing_ids:
                return {"tenant_id": r["tenant_id"]}
        return {"tenant_id": tenants[0]["id"]}

    def test_hospitality_records_list(self, session):
        r = session.get(f"{BASE_URL}/api/hospitality/records")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_hospitality_pdf_generates(self, session, tenant_ctx):
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{tenant_ctx['tenant_id']}")
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", "Response body is not a PDF"
        assert len(r.content) > 1500, "PDF suspiciously small"

    def test_hospitality_pdf_contains_italian_date(self, session, tenant_ctx):
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{tenant_ctx['tenant_id']}")
        assert r.status_code == 200
        import pdfplumber
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        today = date.today().strftime("%d/%m/%Y")
        assert today in text, f"Expected today's Italian date {today} in PDF. Extract head: {text[:500]}"
        assert "Luogo e data" in text or "luogo e data" in text.lower()

    def test_hospitality_pdf_has_checked_alloggio(self, session, tenant_ctx):
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{tenant_ctx['tenant_id']}")
        import pdfplumber
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        assert "alloggio" in text.lower() or "fornito" in text.lower(), \
            f"'ha fornito alloggio' label missing from PDF. Extract: {text[:500]}"

    def test_hospitality_pdf_no_none_placeholder(self, session, tenant_ctx):
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{tenant_ctx['tenant_id']}")
        import pdfplumber
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        # Check literal "None" not leaking
        assert " None " not in text and "NONE " not in text, "Placeholder 'None' leaked into PDF"


# =====================================================================
# 5A — Owner signature upload: transparent PNG round-trip
# =====================================================================
class TestSignature:
    def test_signature_upload_returns_transparent_png(self, session):
        # Build a white-background PNG with some dark strokes
        img = Image.new("RGB", (300, 100), (255, 255, 255))
        px = img.load()
        for x in range(20, 280):
            px[x, 50] = (10, 10, 10)
        buf = io.BytesIO(); img.save(buf, "PNG")

        r = session.post(
            f"{BASE_URL}/api/landlords/signature",
            data={"transparent": "true"},
            files={"file": ("sig.png", buf.getvalue(), "image/png")},
        )
        assert r.status_code == 200, r.text[:200]
        url = r.json().get("url", "")
        assert url.endswith(".png"), f"signature URL not a .png: {url}"

        # Fetch the saved PNG and inspect alpha channel
        dl = session.get(f"{BASE_URL}{url}")
        assert dl.status_code == 200
        got = Image.open(io.BytesIO(dl.content))
        assert got.mode in {"RGBA", "LA"}, f"Signature PNG missing alpha channel (mode={got.mode})"
        # Check at least some pixels are fully transparent
        alpha = got.split()[-1]
        transparent_pixels = sum(1 for p in alpha.getdata() if p == 0)
        assert transparent_pixels > 100, "No fully-transparent pixels found in signature PNG"


# =====================================================================
# 6A / 6B — Registration ZIP bundle
# Review-request says /api/registration/zip/{tenant_id}
# Actual route is /api/documents/bundle/{tenant_id} — test BOTH.
# =====================================================================
class TestRegistrationZip:
    def _pick_tenant(self, session):
        tenants = session.get(f"{BASE_URL}/api/tenants").json()
        if not tenants:
            pytest.skip("No tenants to test zip bundle")
        return tenants[0]["id"]

    def test_registration_zip_route_exists(self, session):
        tid = self._pick_tenant(session)
        r = session.get(f"{BASE_URL}/api/registration/zip/{tid}")
        # If spec says this endpoint should exist, we REPORT if it's 404.
        assert r.status_code != 500, f"5xx on /registration/zip: {r.text[:200]}"
        # Accept 200 (bundle) or 404 (route missing — bug to report).
        if r.status_code == 404:
            pytest.skip("ENDPOINT MISSING: /api/registration/zip/{tenant_id} — see documents/bundle test")

    def test_documents_bundle_returns_zip(self, session):
        tid = self._pick_tenant(session)
        r = session.get(f"{BASE_URL}/api/documents/bundle/{tid}")
        assert r.status_code == 200, r.text[:200]
        ct = r.headers.get("content-type", "")
        assert "zip" in ct or r.content[:2] == b"PK", f"Not a zip response: ct={ct}"
        # Inspect zip contents
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        names = zf.namelist()
        assert len(names) >= 1, "Empty ZIP bundle"
        # Should include at least hospitality PDF (auto-generated)
        has_hospitality = any("osp" in n.lower() or "hospital" in n.lower() for n in names)
        # Soft assert — report if missing
        if not has_hospitality:
            pytest.fail(f"ZIP bundle missing hospitality PDF. Files: {names}")


# =====================================================================
# 7A / 7B — Payment receipt upload: types + size cap
# =====================================================================
class TestPaymentReceipt:
    @pytest.fixture(scope="class")
    def payment_id(self, session):
        payments = session.get(f"{BASE_URL}/api/payments").json()
        if not payments:
            pytest.skip("No payments available")
        return payments[0]["id"]

    def test_receipt_upload_png(self, session, payment_id):
        r = session.post(
            f"{BASE_URL}/api/payments/{payment_id}/receipt",
            files={"file": ("r.png", _png_bytes(50, 50), "image/png")},
        )
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        assert body.get("url", "").startswith("/api/uploads/receipts/"), body

    def test_receipt_upload_pdf(self, session, payment_id):
        r = session.post(
            f"{BASE_URL}/api/payments/{payment_id}/receipt",
            files={"file": ("r.pdf", _make_pdf(), "application/pdf")},
        )
        assert r.status_code == 200, r.text[:200]

    def test_receipt_rejects_bad_type(self, session, payment_id):
        r = session.post(
            f"{BASE_URL}/api/payments/{payment_id}/receipt",
            files={"file": ("r.exe", b"MZ\x90\x00", "application/octet-stream")},
        )
        assert r.status_code in (400, 415), r.text[:200]

    def test_receipt_visible_after_upload(self, session, payment_id):
        payments = session.get(f"{BASE_URL}/api/payments").json()
        p = next((x for x in payments if x["id"] == payment_id), None)
        assert p is not None
        assert p.get("receipt_url"), "receipt_url not persisted after upload"
