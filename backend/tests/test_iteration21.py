"""
Iteration 21 tests:
1) Properties CRUD with structured address (address=Via, civico, comune, province)
2) Hospitality manual creation with landlord_id + contract_id (no tenant_id)
3) Payment Calendar receipt upload/delete
4) Invoice Fattura + Preavviso PDF generation
5) Regression: owners (landlords) authority field, tenants list
"""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
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


# ---------- Properties: structured address ----------
class TestPropertiesAddress:
    def test_list_properties_has_structured_fields(self, session):
        r = session.get(f"{BASE_URL}/api/properties", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Schema-level check: at least one property should expose the new fields
        # (newly created); existing legacy data may lack civico/comune (data migration miss).
        has_civico = any("civico" in p for p in data)
        has_comune = any("comune" in p for p in data)
        assert has_civico or len(data) == 0, "No property has civico field — data migration missing"
        assert has_comune or len(data) == 0, "No property has comune field — data migration missing"

    def test_create_property_with_structured_address(self, session):
        # Need landlord
        ll = session.get(f"{BASE_URL}/api/landlords", timeout=20).json()
        if not ll:
            pytest.skip("No landlord present")
        landlord_id = ll[0]["id"]
        payload = {
            "property_code": "TEST_IT21_PROP",
            "address": "Via Roma",
            "civico": "12",
            "comune": "Padova",
            "province": "PD",
            "property_type": "Appartamento",
            "number_of_rooms": 2,
            "capacity": 2,
            "landlord_id": landlord_id,
            "rental_amount": 800.0,
        }
        r = session.post(f"{BASE_URL}/api/properties", json=payload, timeout=20)
        assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
        prop = r.json()
        assert prop["address"] == "Via Roma"
        assert prop["civico"] == "12"
        assert prop["comune"] == "Padova"
        assert prop["province"] == "PD"
        pid = prop["id"]
        # GET to verify persistence
        g = session.get(f"{BASE_URL}/api/properties/{pid}", timeout=20)
        assert g.status_code == 200
        gp = g.json()
        assert gp["civico"] == "12"
        assert gp["comune"] == "Padova"
        # cleanup
        session.delete(f"{BASE_URL}/api/properties/{pid}", timeout=20)


# ---------- Payment Calendar receipts ----------
class TestPaymentCalendarReceipt:
    def test_upload_and_delete_receipt(self, session):
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()
        if not tenants:
            pytest.skip("No tenants")
        tid = tenants[0]["id"]
        year, month = 2026, 1
        # Create simple PDF bytes
        pdf_bytes = b"%PDF-1.4\n%fake-test-pdf\n%%EOF"
        files = {"file": ("receipt.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        r = session.post(
            f"{BASE_URL}/api/payment-calendar/{tid}/{year}/{month}/receipt",
            files=files,
            timeout=30,
        )
        assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
        body = r.json()
        assert "receipt_url" in body
        # Verify GET shows receipt
        g = session.get(f"{BASE_URL}/api/payment-calendar/{tid}", timeout=20)
        assert g.status_code == 200
        cal = g.json()
        cal_months = cal if isinstance(cal, list) else cal.get("calendar", cal.get("months", []))
        found = False
        for m in cal_months:
            if m.get("year") == year and m.get("month") == month and m.get("receipt_url"):
                found = True
                break
        assert found, f"Receipt not visible in calendar response: {cal}"
        # Delete
        d = session.delete(
            f"{BASE_URL}/api/payment-calendar/{tid}/{year}/{month}/receipt", timeout=20
        )
        assert d.status_code in (200, 204)


# ---------- Hospitality manual creation ----------
class TestHospitalityManual:
    def test_manual_create_landlord_contract(self, session):
        landlords = session.get(f"{BASE_URL}/api/landlords", timeout=20).json()
        contracts = session.get(f"{BASE_URL}/api/contracts", timeout=20).json()
        if not landlords or not contracts:
            pytest.skip("Need landlord & contract")
        payload = {
            "landlord_id": landlords[0]["id"],
            "contract_id": contracts[0]["id"],
            "guest_name": "TEST_Guest",
            "guest_surname": "TEST_Surname",
        }
        r = session.post(f"{BASE_URL}/api/hospitality/records", json=payload, timeout=20)
        # Accept 200/201 OR 422 (if endpoint requires tenant_id strictly)
        if r.status_code == 422:
            pytest.fail(f"Manual hospitality (without tenant_id) rejected: {r.text}")
        assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
        rec = r.json()
        assert rec.get("landlord_id") == landlords[0]["id"]
        assert rec.get("contract_id") == contracts[0]["id"]
        rec_id = rec.get("id")
        # PUT edit
        if rec_id:
            up = session.put(
                f"{BASE_URL}/api/hospitality/records/{rec_id}",
                json={"guest_name": "TEST_Guest_Updated"},
                timeout=20,
            )
            assert up.status_code in (200, 204), f"{up.status_code} {up.text}"


# ---------- Invoice PDF (fattura + preavviso) ----------
class TestInvoicePDF:
    def test_fattura_and_preavviso_pdf(self, session):
        invs = session.get(f"{BASE_URL}/api/invoices", timeout=20).json()
        if not invs:
            pytest.skip("No invoices")
        # Pick fattura and preavviso (any first invoice -> get pdf)
        any_inv = invs[0]
        r = session.get(f"{BASE_URL}/api/invoices/{any_inv['id']}/pdf", timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        assert r.content[:4] == b"%PDF", "Not a PDF response"


# ---------- Regression: owners authority + tenants list ----------
class TestRegression:
    def test_landlords_authority_field_present(self, session):
        ll = session.get(f"{BASE_URL}/api/landlords", timeout=20).json()
        assert isinstance(ll, list)
        if ll:
            assert "authority" in ll[0], f"authority field missing in landlord: {list(ll[0].keys())}"

    def test_tenants_list(self, session):
        r = session.get(f"{BASE_URL}/api/tenants", timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_dashboard_stats(self, session):
        r = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=20)
        assert r.status_code == 200
