"""
Iteration 23 tests: Branding + UI regression.
Verify backend regression + PDF/email branding swap to "Housing in Padova".
"""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "test-bypass"},
        timeout=20,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def ids(session):
    landlords = session.get(f"{BASE_URL}/api/landlords", timeout=20).json()
    contracts = session.get(f"{BASE_URL}/api/contracts", timeout=20).json()
    tenants = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()
    properties = session.get(f"{BASE_URL}/api/properties", timeout=20).json()
    invoices = session.get(f"{BASE_URL}/api/invoices", timeout=20).json()
    return {
        "landlord_id": landlords[0]["id"] if landlords else None,
        "contract_id": contracts[0]["id"] if contracts else None,
        "tenant_id": tenants[0]["id"] if tenants else None,
        "property_id": properties[0]["id"] if properties else None,
        "invoice_id": invoices[0]["id"] if invoices else None,
    }


# ---------- Core CRUD smoke ----------
class TestCoreCRUDSmoke:
    def test_auth_me(self, session):
        r = session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        assert r.json().get("email") == ADMIN_EMAIL

    def test_properties_normalization(self, session):
        r = session.get(f"{BASE_URL}/api/properties", timeout=20)
        assert r.status_code == 200
        for p in r.json():
            assert "civico" in p and "comune" in p and "province" in p

    def test_tenants(self, session):
        r = session.get(f"{BASE_URL}/api/tenants", timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_landlords_authority(self, session):
        r = session.get(f"{BASE_URL}/api/landlords", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            assert "authority" in data[0]

    def test_contracts(self, session):
        r = session.get(f"{BASE_URL}/api/contracts", timeout=20)
        assert r.status_code == 200

    def test_dashboard_stats(self, session):
        r = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=20)
        assert r.status_code == 200

    def test_hospitality_records_list(self, session):
        r = session.get(f"{BASE_URL}/api/hospitality/records", timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- PDF generation: %PDF header ----------
class TestPDFGeneration:
    def test_invoice_pdf(self, session, ids):
        if not ids["invoice_id"]:
            pytest.skip("no invoice")
        r = session.get(f"{BASE_URL}/api/invoices/{ids['invoice_id']}/pdf", timeout=30)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF", f"Invoice not PDF: {r.content[:20]}"

    def test_hospitality_pdf_tenant(self, session, ids):
        if not ids["tenant_id"]:
            pytest.skip("no tenant")
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{ids['tenant_id']}", timeout=30)
        # Tenant might not have hospitality record; accept 200/404
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            assert r.content[:4] == b"%PDF"

    def test_contract_pdf(self, session, ids):
        if not ids["contract_id"]:
            pytest.skip("no contract")
        r = session.get(f"{BASE_URL}/api/contracts/{ids['contract_id']}/pdf", timeout=30)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            assert r.content[:4] == b"%PDF"


# ---------- Manual hospitality (iter22 regression) ----------
class TestHospitalityManual:
    rid = None

    def test_post_manual(self, session, ids):
        if not (ids["landlord_id"] and ids["contract_id"]):
            pytest.skip("need landlord+contract")
        payload = {
            "mode": "manual",
            "landlord_id": ids["landlord_id"],
            "contract_id": ids["contract_id"],
            "guest_surname": "TEST_IT23",
            "guest_name": "Branding",
            "guest_nationality": "ITA",
            "guest_passport": "B2301",
        }
        r = session.post(f"{BASE_URL}/api/hospitality/records", json=payload, timeout=20)
        assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
        rec = r.json()
        assert rec.get("mode") == "manual"
        TestHospitalityManual.rid = rec["id"]

    def test_pdf_manual(self, session):
        rid = TestHospitalityManual.rid
        if not rid:
            pytest.skip("no manual record")
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/record/{rid}", timeout=30)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"

    def test_cleanup(self, session):
        rid = TestHospitalityManual.rid
        if rid:
            session.delete(f"{BASE_URL}/api/hospitality/records/{rid}", timeout=20)


# ---------- OCR ----------
class TestOCR:
    def test_ocr_scan_small_image(self, session):
        # 1x1 white PNG
        png_bytes = bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
            "0000000D49444154789C62F8FFFF3F0300050001FFA5D9C2720000000049454E44AE426082"
        )
        files = {"file": ("pixel.png", png_bytes, "image/png")}
        r = session.post(f"{BASE_URL}/api/ocr/scan", files=files, timeout=60)
        # OCR may 200 with empty fields or 400/422; we just ensure endpoint responds without 5xx
        assert r.status_code < 500, f"OCR 5xx: {r.status_code} {r.text[:200]}"


# ---------- Branding verification (code-level) ----------
class TestBrandingCode:
    def test_email_template_contains_housing_in_padova(self):
        with open("/app/backend/services/email_reminders.py", "r", encoding="utf-8") as f:
            content = f.read()
        assert "Housing in Padova" in content
        # the lowercase old brand on its own should not appear
        assert "Consulenze immobiliari" not in content, "old brand text (lowercase 'i') still present"

    def test_ricevuta_pdf_contains_housing_in_padova(self):
        with open("/app/backend/services/ricevuta_pdf.py", "r", encoding="utf-8") as f:
            content = f.read()
        assert "Housing in Padova" in content

    def test_invoice_generator_contains_housing_in_padova(self):
        with open("/app/backend/invoice_generator.py", "r", encoding="utf-8") as f:
            content = f.read()
        assert 'company_name = "Housing in Padova"' in content or '"Housing in Padova"' in content
