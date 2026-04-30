"""Iteration 17 — Room reassignment fix, Property photo gallery (backend side),
Fattura PDF, Preavviso PDF."""
import os
import uuid
import pytest
import requests
from datetime import datetime, timedelta

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    return url.rstrip("/")


BASE_URL = _load_backend_url()
ADMIN_EMAIL = "nazaninalizade890@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


# ----------------------------- Fixtures ----------------------------------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "test"},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def seed_data(session):
    """Create landlord -> property -> 1 room -> 2 tenants. Cleanup at end."""
    landlord = None
    landlords = session.get(f"{BASE_URL}/api/landlords", timeout=15).json()
    if landlords:
        landlord = landlords[0]
    else:
        r = session.post(
            f"{BASE_URL}/api/landlords",
            json={
                "surname": "TESTIT17",
                "name": "Owner",
                "full_name": "TESTIT17 Owner",
                "codice_fiscale": "TSTOWN00A00A000A",
                "id_number": "CI12345678",
                "bank_details": "IBAN TEST",
                "phone": "+39 333 1234567",
                "email": "testit17@example.com",
                "address": "Via Test 1",
                "city": "Padova",
                "province": "PD",
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        landlord = r.json()

    rp = session.post(
        f"{BASE_URL}/api/properties",
        json={
            "address": f"TEST_IT17 Via Roma {uuid.uuid4().hex[:4]}",
            "property_type": "apartment",
            "number_of_rooms": 1,
            "capacity": 2,
            "rental_amount": 900,
            "landlord_id": landlord["id"],
            "province": "PD",
            "phone": "+39 333 1234567",
        },
        timeout=15,
    )
    assert rp.status_code == 200, rp.text
    prop = rp.json()

    rr = session.post(
        f"{BASE_URL}/api/rooms",
        json={"property_id": prop["id"], "room_number": "1", "room_type": "singola",
              "monthly_rent": 450.0, "description": "", "bill_responsible": ""},
        timeout=15,
    )
    assert rr.status_code == 200, rr.text
    room = rr.json()

    tenants_created = []
    for i in range(2):
        rt = session.post(
            f"{BASE_URL}/api/tenants",
            json={
                "full_name": f"TESTIT17 Tenant{i}",
                "passport_number": f"P{uuid.uuid4().hex[:8]}",
                "nationality": "Italiana",
                "date_of_birth": "1990-01-01",
                "passport_issue_date": "2020-01-01",
                "passport_expiry_date": "2030-01-01",
                "email": f"testit17_{i}_{uuid.uuid4().hex[:4]}@example.com",
            },
            timeout=15,
        )
        assert rt.status_code == 200, rt.text
        tenants_created.append(rt.json())

    data = {
        "landlord_id": landlord["id"],
        "property_id": prop["id"],
        "room_id": room["id"],
        "tenant_ids": [t["id"] for t in tenants_created],
    }
    yield data

    # Cleanup
    for tid in data["tenant_ids"]:
        try:
            session.delete(f"{BASE_URL}/api/tenants/{tid}", timeout=10)
        except Exception:
            pass
    try:
        session.delete(f"{BASE_URL}/api/rooms/{data['room_id']}", timeout=10)
        session.delete(f"{BASE_URL}/api/properties/{data['property_id']}", timeout=10)
    except Exception:
        pass


# =========================================================================
# A) BUG FIX — Room reassignment must free previous occupant
# =========================================================================
class TestRoomReassignment:
    def test_reassign_room_frees_previous_occupant(self, session, seed_data):
        room_id = seed_data["room_id"]
        t1, t2 = seed_data["tenant_ids"]

        # Assign t1 to room
        r = session.post(f"{BASE_URL}/api/rooms/{room_id}/assign",
                         data={"tenant_id": t1}, timeout=15)
        assert r.status_code == 200, r.text
        room = session.get(f"{BASE_URL}/api/rooms/{room_id}", timeout=15).json()
        assert room["tenant_id"] == t1
        assert room["status"] == "occupied"
        t1_obj = session.get(f"{BASE_URL}/api/tenants/{t1}", timeout=15).json()
        assert t1_obj["room_id"] == room_id

        # Reassign same room to t2 — must free t1
        r2 = session.post(f"{BASE_URL}/api/rooms/{room_id}/assign",
                          data={"tenant_id": t2}, timeout=15)
        assert r2.status_code == 200, r2.text

        room2 = session.get(f"{BASE_URL}/api/rooms/{room_id}", timeout=15).json()
        assert room2["tenant_id"] == t2
        assert room2["status"] == "occupied"

        # Verify t1 no longer references this room (BUG FIX)
        t1_after = session.get(f"{BASE_URL}/api/tenants/{t1}", timeout=15).json()
        assert t1_after["room_id"] in ("", None), \
            f"BUG: previous occupant t1 still has room_id={t1_after['room_id']}"
        assert t1_after.get("property_id") in ("", None)

        # Verify t2 now references this room
        t2_after = session.get(f"{BASE_URL}/api/tenants/{t2}", timeout=15).json()
        assert t2_after["room_id"] == room_id

        # Unassign cleanup
        session.post(f"{BASE_URL}/api/rooms/{room_id}/unassign", timeout=15)


# =========================================================================
# B) FEATURE 9 — Property photo gallery backend (upload + delete)
# =========================================================================
class TestPropertyGallery:
    def test_upload_and_delete_property_image(self, session, seed_data):
        prop_id = seed_data["property_id"]
        # 1x1 PNG bytes
        png_bytes = bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
            "89000000094944415478DA63600000000005000100A5F645400000000049454E"
            "44AE426082"
        )
        files = {"file": ("test.png", png_bytes, "image/png")}
        r = session.post(f"{BASE_URL}/api/properties/{prop_id}/images",
                         files=files, timeout=15)
        assert r.status_code == 200, r.text
        url = r.json()["url"]
        assert url.startswith("/api/uploads/properties/")

        prop = session.get(f"{BASE_URL}/api/properties/{prop_id}", timeout=15).json()
        assert url in prop.get("images", [])

        # Delete via DELETE query param
        rd = session.delete(f"{BASE_URL}/api/properties/{prop_id}/images",
                            params={"url": url}, timeout=15)
        assert rd.status_code == 200, rd.text
        prop2 = session.get(f"{BASE_URL}/api/properties/{prop_id}", timeout=15).json()
        assert url not in prop2.get("images", [])


# =========================================================================
# C) FEATURE 12 — Fattura PDF
# =========================================================================
class TestFatturaPDF:
    def test_create_fattura_and_download_pdf(self, session, seed_data):
        tenant_id = seed_data["tenant_ids"][0]
        prop_id = seed_data["property_id"]
        due = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

        payload = {
            "tenant_id": tenant_id,
            "property_id": prop_id,
            "contract_id": "",
            "invoice_type": "rent",
            "amount": 1100.0,
            "due_date": due,
            "description": "Ricerca inquilino per appartamento test",
            "document_type": "fattura",
            "rent": 900.0,
            "agency_fee": 200.0,
            "imponibile": 1100.0,
            "vat_rate": 22.0,
        }
        r = session.post(f"{BASE_URL}/api/invoices", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        invoice = r.json()
        assert invoice.get("document_type") == "fattura"
        assert invoice.get("imponibile") == 1100.0
        assert invoice.get("vat_rate") == 22.0
        inv_id = invoice["id"]

        # Verify GET persistence
        g = session.get(f"{BASE_URL}/api/invoices/{inv_id}", timeout=15).json()
        assert g["document_type"] == "fattura"

        # PDF download
        pdf_resp = session.get(f"{BASE_URL}/api/invoices/{inv_id}/pdf", timeout=20)
        assert pdf_resp.status_code == 200
        assert "application/pdf" in pdf_resp.headers.get("content-type", "")
        assert pdf_resp.content[:4] == b"%PDF", "Not a valid PDF"
        assert len(pdf_resp.content) >= 1500, f"PDF too small: {len(pdf_resp.content)}"

        session.delete(f"{BASE_URL}/api/invoices/{inv_id}", timeout=10)


# =========================================================================
# D) FEATURE 13 — Preavviso PDF (no tenant / no property)
# =========================================================================
class TestPreavvisoPDF:
    def test_create_preavviso_without_tenant_and_download_pdf(self, session):
        due = (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d")
        payload = {
            "tenant_id": "",
            "property_id": "",
            "contract_id": "",
            "invoice_type": "other",
            "amount": 1772.0,  # imponibile*(1+vat/100) + rimborso = 1300*1.22 + 186
            "due_date": due,
            "description": "Preavviso test",
            "document_type": "preavviso",
            "recipient_name": "TESTIT17 ELEISON Cooperativa",
            "recipient_address": "Via Pulle 15/17 Padova",
            "recipient_cf_piva": "05028740289",
            "body_text": "Ricerca appartamento in locazione Padova Via Mozart",
            "imponibile": 1300.0,
            "vat_rate": 22.0,
            "rimborso_label": "Rimborso spese registrazione contratto",
            "rimborso_amount": 186.0,
            "rimborso_note": "(Imposta di bollo non presente)",
            "rimborso_tax_note": "(esente iva art 15)",
        }
        r = session.post(f"{BASE_URL}/api/invoices", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        invoice = r.json()
        assert invoice["document_type"] == "preavviso"
        assert invoice["recipient_name"] == "TESTIT17 ELEISON Cooperativa"
        assert invoice["tenant_name"] == "TESTIT17 ELEISON Cooperativa"  # fallback
        assert invoice["imponibile"] == 1300.0
        assert invoice["rimborso_amount"] == 186.0

        # Verify total math sanity
        total_expected = round(1300.0 * (1 + 22.0 / 100) + 186.0, 2)
        assert total_expected == 1772.0

        inv_id = invoice["id"]
        pdf_resp = session.get(f"{BASE_URL}/api/invoices/{inv_id}/pdf", timeout=20)
        assert pdf_resp.status_code == 200
        assert "application/pdf" in pdf_resp.headers.get("content-type", "")
        assert pdf_resp.content[:4] == b"%PDF"
        assert len(pdf_resp.content) >= 1500

        session.delete(f"{BASE_URL}/api/invoices/{inv_id}", timeout=10)


# =========================================================================
# F) Light regression smoke
# =========================================================================
class TestRegressionSmoke:
    def test_list_tenants(self, session):
        r = session.get(f"{BASE_URL}/api/tenants", timeout=15)
        assert r.status_code == 200

    def test_list_properties(self, session):
        r = session.get(f"{BASE_URL}/api/properties", timeout=15)
        assert r.status_code == 200

    def test_dashboard_stats(self, session):
        r = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=15)
        assert r.status_code == 200
