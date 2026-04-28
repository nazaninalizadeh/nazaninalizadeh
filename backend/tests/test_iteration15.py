"""Iteration 15 backend tests:
Group 1+2+3 batch updates.
- Properties API: single_rooms_count + double_rooms_count fields, create with property_type/province/phone
- DELETE /api/contracts/{id} 200 / 404
- DELETE /api/payments/{id} 200 / 404 + invoice paid_amount reversal
- Rooms POST without 'floor' field works (no floor in schema)
- Tenants list returns room_type and room_rent
- OCR: PDF upload not rejected (content_type=application/pdf accepted)
- OCR: country_of_birth code translation _country_from_code returns Italian names
- Hospitality PDF: 'Luogo e data: <City>, DD/MM/YYYY' (title-cased), signature image overlay (smoke)
- Landlord signature upload: PNG transparent ok; .txt -> 400; >5MB -> 413
- Schema back-compat: TenantCreate.whatsapp + LandlordCreate.whatsapp Optional with default ''
"""
import os
import io
import re
import sys
import asyncio
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
ADMIN2_EMAIL = "nazaninalizade890@gmail.com"
ADMIN2_PASSWORD = "1234@Admin"

sys.path.insert(0, "/app/backend")


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN2_EMAIL,
        "password": ADMIN2_PASSWORD,
        "captcha_token": "",
    }, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Auth failed: {r.status_code} {r.text}")
    return s


# ============ Properties ============
class TestPropertiesEnrichedFields:
    def test_get_properties_includes_room_type_counts(self, session):
        r = session.get(f"{BASE_URL}/api/properties", timeout=20)
        assert r.status_code == 200
        props = r.json()
        assert isinstance(props, list)
        if not props:
            pytest.skip("no properties to verify")
        for p in props:
            assert "single_rooms_count" in p, f"missing single_rooms_count in {p.get('id')}"
            assert "double_rooms_count" in p, f"missing double_rooms_count in {p.get('id')}"
            assert isinstance(p["single_rooms_count"], int)
            assert isinstance(p["double_rooms_count"], int)

    def test_create_property_with_new_fields(self, session):
        landlords = session.get(f"{BASE_URL}/api/landlords", timeout=15).json()
        if not landlords:
            pytest.skip("no landlord to attach property to")
        ll = landlords[0]
        payload = {
            "address": "Via TEST_iter15 12, Padova",
            "property_type": "Appartamento",
            "number_of_rooms": 2,
            "capacity": 3,
            "landlord_id": ll["id"],
            "rental_amount": 1200.0,
            "additional_charges": "",
            "province": "PD",
            "phone": "+393331112222",
        }
        r = session.post(f"{BASE_URL}/api/properties", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["address"] == payload["address"]
        assert body.get("property_type") == "Appartamento"
        assert body.get("province") == "PD"
        assert body.get("phone") == "+393331112222"
        pid = body["id"]
        # GET to verify persistence
        g = session.get(f"{BASE_URL}/api/properties/{pid}", timeout=15).json()
        assert g["province"] == "PD"
        assert g["property_type"] == "Appartamento"
        assert g["phone"] == "+393331112222"
        # Cleanup
        session.delete(f"{BASE_URL}/api/properties/{pid}", timeout=15)


# ============ Rooms (no floor field) ============
class TestRoomsNoFloor:
    def test_create_room_without_floor(self, session):
        landlords = session.get(f"{BASE_URL}/api/landlords", timeout=15).json()
        if not landlords:
            pytest.skip("no landlord")
        # Create temp property
        prop_payload = {
            "address": "Via TEST_iter15_room 1",
            "property_type": "Appartamento",
            "number_of_rooms": 1,
            "capacity": 1,
            "landlord_id": landlords[0]["id"],
            "rental_amount": 500.0,
            "province": "PD",
            "phone": "",
        }
        pr = session.post(f"{BASE_URL}/api/properties", json=prop_payload, timeout=20)
        assert pr.status_code == 200, pr.text
        pid = pr.json()["id"]
        try:
            payload = {
                "property_id": pid,
                "room_number": "T1",
                "room_type": "double",
                "monthly_rent": 700.0,
            }
            r = session.post(f"{BASE_URL}/api/rooms", json=payload, timeout=15)
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["room_number"] == "T1"
            assert data["room_type"] == "double"
            assert data["monthly_rent"] == 700.0
            # Field 'floor' should NOT be in response
            assert "floor" not in data
        finally:
            session.delete(f"{BASE_URL}/api/properties/{pid}", timeout=15)


# ============ Tenants enriched (room_type + room_rent) ============
class TestTenantsEnrichedRoom:
    def test_tenant_list_has_room_type_and_rent(self, session):
        r = session.get(f"{BASE_URL}/api/tenants", timeout=20)
        assert r.status_code == 200
        for t in r.json():
            assert "room_type" in t
            assert "room_rent" in t


# ============ DELETE Contracts ============
class TestDeleteContract:
    def test_delete_nonexistent_contract_404(self, session):
        r = session.delete(f"{BASE_URL}/api/contracts/nonexistent_xyz_iter15", timeout=15)
        assert r.status_code == 404

    def test_delete_contract_lifecycle(self, session):
        # Find an existing contract OR create one quickly
        contracts = session.get(f"{BASE_URL}/api/contracts", timeout=15).json()
        if not contracts:
            pytest.skip("no contracts to delete-test")
        # Pick one to delete - use the last one (least likely to be needed)
        cid = contracts[-1]["id"]
        r = session.delete(f"{BASE_URL}/api/contracts/{cid}", timeout=15)
        assert r.status_code == 200, r.text
        # Second delete -> 404
        r2 = session.delete(f"{BASE_URL}/api/contracts/{cid}", timeout=15)
        assert r2.status_code == 404


# ============ DELETE Payments ============
class TestDeletePayment:
    def test_delete_nonexistent_payment_404(self, session):
        r = session.delete(f"{BASE_URL}/api/payments/nonexistent_xyz_iter15", timeout=15)
        assert r.status_code == 404

    def test_delete_payment_reverses_invoice(self, session):
        # Find an invoice with a payment
        invoices = session.get(f"{BASE_URL}/api/invoices", timeout=15).json()
        target_inv = None
        for inv in invoices:
            if inv.get("paid_amount", 0) > 0:
                target_inv = inv
                break
        if not target_inv:
            pytest.skip("no paid invoices to test reversal")
        # Get payments for that invoice
        all_payments = session.get(f"{BASE_URL}/api/payments", timeout=15).json()
        related = [p for p in all_payments if p.get("invoice_id") == target_inv["id"]]
        if not related:
            pytest.skip("no payment linked to paid invoice")
        pay = related[0]
        original_paid = target_inv["paid_amount"]
        amount = pay["amount"]
        r = session.delete(f"{BASE_URL}/api/payments/{pay['id']}", timeout=15)
        assert r.status_code == 200
        # Verify invoice paid_amount reduced
        inv2 = session.get(f"{BASE_URL}/api/invoices", timeout=15).json()
        updated = [i for i in inv2 if i["id"] == target_inv["id"]]
        if updated:
            new_paid = updated[0].get("paid_amount", 0)
            assert new_paid == max(0, original_paid - amount), \
                f"paid_amount expected {original_paid - amount}, got {new_paid}"


# ============ OCR PDF acceptance ============
class TestOCRPDFAccept:
    def test_pdf_content_type_not_rejected_400(self, session):
        # Send a tiny dummy PDF — must not return 400 (was rejected before)
        pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
        files = {"file": ("test_iter15.pdf", pdf_bytes, "application/pdf")}
        r = session.post(f"{BASE_URL}/api/ocr/scan", files=files, timeout=120)
        # Either 200 (LLM ran or fell back) or 5xx for LLM error — must NOT be 400 unsupported
        assert r.status_code != 400 or "Formato non supportato" not in r.text, \
            f"PDF rejected as unsupported format: {r.status_code} {r.text[:200]}"
        # Acceptable outcomes: 200 (success or extracted data even partial)
        # Or 422/500 if LLM/PIL fails — that's ok, just confirms the type guard accepts PDF
        assert r.status_code in (200, 422, 500, 502, 503), f"unexpected status {r.status_code}: {r.text[:200]}"


# ============ OCR country code translation (unit) ============
class TestOCRCountryCode:
    def test_country_from_code_translations(self):
        from services.ocr_service import _country_from_code
        assert _country_from_code("IRN") == "Iran"
        assert _country_from_code("ITA") == "Italia"
        assert _country_from_code("FRA") == "Francia"
        assert _country_from_code("DEU") == "Germania"
        assert _country_from_code("MAR") == "Marocco"
        # Empty/unknown
        assert _country_from_code("") == ""


# ============ Hospitality PDF signature line + city title-case ============
class TestHospitalityPDFSignature:
    def test_pdf_returns_200_and_has_luogo_padova(self, session):
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=15).json()
        if not tenants:
            pytest.skip("no tenants")
        tid = tenants[0]["id"]
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{tid}", timeout=30)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
        # Extract text and verify "Luogo e data:" present
        try:
            from pypdf import PdfReader
        except Exception:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except Exception:
                pytest.skip("no pdf reader installed")
        reader = PdfReader(io.BytesIO(r.content))
        text = "".join((p.extract_text() or "") for p in reader.pages)
        assert "Luogo e data:" in text, f"missing 'Luogo e data:' string. snippet={text[-500:]}"
        # Date format DD/MM/YYYY appears somewhere in signature line
        m = re.search(r"Luogo e data:\s*([^,]*),\s*(\d{2}/\d{2}/\d{4})", text)
        assert m, f"signature date line not in DD/MM/YYYY format: {text[-400:]}"
        city = m.group(1).strip()
        # City should NOT be all uppercase (title-cased)
        if city:
            assert city != city.upper() or len(city) <= 2, f"city '{city}' looks all-uppercase, expected title-case"


# ============ Landlord signature upload ============
class TestLandlordSignatureUpload:
    def _make_png(self, w=20, h=20):
        try:
            from PIL import Image
        except Exception:
            pytest.skip("PIL not available")
        img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        # Add some dark pixels so transparent conversion has something to keep
        for x in range(w // 2):
            for y in range(h // 2):
                img.putpixel((x, y), (10, 10, 10, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_upload_png_with_transparent_returns_url(self, session):
        png = self._make_png()
        files = {"file": ("sig.png", png, "image/png")}
        data = {"transparent": "true"}
        r = session.post(f"{BASE_URL}/api/landlords/signature", files=files, data=data, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "url" in body
        assert body["url"].startswith("/api/uploads/signatures/")
        # Download and verify it's a PNG (transparent processing produces PNG)
        full = f"{BASE_URL}{body['url']}"
        r2 = session.get(full, timeout=15, allow_redirects=False)
        assert r2.status_code == 200
        assert r2.content[:8] == b"\x89PNG\r\n\x1a\n", "uploaded signature not a PNG"

    def test_upload_txt_rejected_400(self, session):
        files = {"file": ("notimg.txt", b"hello", "text/plain")}
        data = {"transparent": "false"}
        r = session.post(f"{BASE_URL}/api/landlords/signature", files=files, data=data, timeout=15)
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"

    def test_upload_too_large_413(self, session):
        # 6MB random bytes with .png extension
        big = b"\x89PNG\r\n\x1a\n" + os.urandom(6 * 1024 * 1024)
        files = {"file": ("big.png", big, "image/png")}
        data = {"transparent": "false"}
        r = session.post(f"{BASE_URL}/api/landlords/signature", files=files, data=data, timeout=60)
        assert r.status_code == 413, f"expected 413, got {r.status_code}: {r.text[:200]}"


# ============ Schema back-compat ============
class TestSchemaBackCompat:
    def test_tenant_create_no_whatsapp_field(self):
        from models.schemas import TenantCreate
        t = TenantCreate(
            full_name="TEST_iter15_NoWA",
            phone="+393330000000",
            passport_number="X1234567",
            nationality="Italiana",
            date_of_birth="1990-01-01",
            passport_issue_date="2020-01-01",
            passport_expiry_date="2030-01-01",
            email="t@example.com",
        )
        d = t.model_dump()
        # whatsapp defaults to empty string (Optional, not required)
        assert d.get("whatsapp", "") == ""

    def test_landlord_create_no_whatsapp_field(self):
        from models.schemas import LandlordCreate
        ll = LandlordCreate(
            full_name="TEST_iter15_LL",
            email="x@example.com",
            phone="+393330000000",
            id_number="ID12345",
            bank_details="IT00X0000000000000000000000",
        )
        d = ll.model_dump()
        assert d.get("whatsapp", "") == ""
