"""Tests for new features: OCR, Hospitality PDF, and Data Exchange (Import/Export)."""
import os
import io
import pytest
import requests
from openpyxl import Workbook

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")


# ------------ Fixtures ------------

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    # login
    resp = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": "alborz.sbd@gmail.com",
        "password": "1234@Admin",
        "captcha_token": "",
    }, timeout=20)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    return s


@pytest.fixture(scope="module")
def test_tenant(session):
    """Create a tenant used for PDF tests."""
    payload = {
        "full_name": "TEST_NewFeatures Mario",
        "email": "test_newfeatures@example.com",
        "phone": "+391234567890",
        "whatsapp": "+391234567890",
        "passport_number": "TEST_PS123",
        "nationality": "Italian",
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "place_of_birth": "Roma",
        "codice_fiscale": "TESTNF90A01H501Z",
        "passport_issue_date": "2020-01-01",
        "passport_expiry_date": "2030-01-01",
        "address": "Via Roma 1, Milano",
        "occupation": "Student",
    }
    r = session.post(f"{BASE_URL}/api/tenants", json=payload, timeout=15)
    assert r.status_code in (200, 201), f"Tenant create failed: {r.text}"
    tenant = r.json()
    yield tenant
    # cleanup
    session.delete(f"{BASE_URL}/api/tenants/{tenant['id']}", timeout=10)


# ------------ Basic API existence ------------

class TestAuth:
    def test_login(self, session):
        r = session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        assert r.json()["email"] == "alborz.sbd@gmail.com"


class TestCoreEndpoints:
    def test_get_tenants(self, session):
        r = session.get(f"{BASE_URL}/api/tenants", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_occupancy_overview(self, session):
        r = session.get(f"{BASE_URL}/api/occupancy-overview", timeout=15)
        assert r.status_code == 200
        data = r.json()
        # expected to be a list or object describing occupancy
        assert data is not None


# ------------ Data Exchange: Templates ------------

class TestTemplates:
    def test_download_tenant_template(self, session):
        r = session.get(f"{BASE_URL}/api/data/templates/tenants", timeout=15)
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "spreadsheet" in ct or "excel" in ct.lower() or "openxml" in ct
        # Excel files start with PK (zip)
        assert r.content[:2] == b"PK"
        assert len(r.content) > 500

    def test_download_payment_template(self, session):
        r = session.get(f"{BASE_URL}/api/data/templates/payments", timeout=15)
        assert r.status_code == 200, r.text
        assert r.content[:2] == b"PK"
        assert len(r.content) > 500


# ------------ Data Exchange: Exports ------------

class TestExports:
    def test_export_tenants(self, session):
        r = session.get(f"{BASE_URL}/api/data/export/tenants", timeout=20)
        assert r.status_code == 200, r.text
        assert r.content[:2] == b"PK"

    def test_export_payments(self, session):
        r = session.get(f"{BASE_URL}/api/data/export/payments", timeout=20)
        assert r.status_code == 200, r.text
        assert r.content[:2] == b"PK"

    def test_export_occupancy(self, session):
        r = session.get(f"{BASE_URL}/api/data/export/occupancy", timeout=20)
        assert r.status_code == 200, r.text
        assert r.content[:2] == b"PK"


# ------------ Data Exchange: Imports ------------

class TestImports:
    def test_import_tenants_invalid_format(self, session):
        files = {"file": ("test.txt", b"some text", "text/plain")}
        r = session.post(f"{BASE_URL}/api/data/import/tenants", files=files, timeout=15)
        assert r.status_code == 400

    def test_import_tenants_csv(self, session):
        csv_content = (
            "full_name,email,phone,passport_number,nationality,date_of_birth,codice_fiscale\n"
            "TEST_ImportCsv Luigi,test_import_csv@example.com,+390000000,IMP_PS111,Italian,1985-05-05,TESTIC85E05H501A\n"
        )
        files = {"file": ("tenants.csv", csv_content.encode("utf-8"), "text/csv")}
        r = session.post(f"{BASE_URL}/api/data/import/tenants", files=files, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "success_count" in body
        assert "error_count" in body
        # Cleanup - find and delete imported tenant
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=15).json()
        for t in tenants:
            if t.get("email") == "test_import_csv@example.com":
                session.delete(f"{BASE_URL}/api/tenants/{t['id']}", timeout=10)


# ------------ Hospitality PDF ------------

class TestHospitalityPDF:
    def test_hospitality_pdf_download(self, session, test_tenant):
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{test_tenant['id']}", timeout=30)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        # PDF starts with %PDF
        assert r.content[:4] == b"%PDF"

    def test_hospitality_pdf_not_found(self, session):
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/nonexistent-id", timeout=15)
        assert r.status_code == 404


# ------------ OCR ------------

class TestOCR:
    def test_ocr_invalid_content_type(self, session):
        files = {"file": ("test.txt", b"hi", "text/plain")}
        r = session.post(f"{BASE_URL}/api/ocr/scan", files=files, timeout=30)
        assert r.status_code == 400

    def test_ocr_scan_with_image(self, session):
        # Minimal valid 1x1 PNG
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf"
            b"\xc0\x00\x00\x00\x03\x00\x01\x1a\xc5\xcb\xc4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        files = {"file": ("test.png", png_bytes, "image/png")}
        r = session.post(f"{BASE_URL}/api/ocr/scan", files=files, timeout=60)
        # OCR may return 200 with partial/empty data OR a proper result; allow both
        # but should not be a 500 (integration failure)
        assert r.status_code in (200, 400, 422), f"Unexpected status {r.status_code}: {r.text}"
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)
