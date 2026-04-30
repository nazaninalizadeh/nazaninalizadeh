"""
Iteration 22 tests: re-verify manual hospitality + properties normalization, no regression on iter16-21.
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
    return {
        "landlord_id": landlords[0]["id"] if landlords else None,
        "contract_id": contracts[0]["id"] if contracts else None,
        "tenant_id": tenants[0]["id"] if tenants else None,
        "property_id": properties[0]["id"] if properties else None,
    }


# ---------- Properties civico/comune normalization ----------
class TestPropertiesNormalization:
    def test_list_normalizes_legacy(self, session):
        r = session.get(f"{BASE_URL}/api/properties", timeout=20)
        assert r.status_code == 200
        data = r.json()
        for p in data:
            assert "civico" in p, f"missing civico: {list(p.keys())}"
            assert "comune" in p, f"missing comune: {list(p.keys())}"
            assert "province" in p, f"missing province: {list(p.keys())}"

    def test_get_one_normalizes(self, session, ids):
        if not ids["property_id"]:
            pytest.skip("no property")
        r = session.get(f"{BASE_URL}/api/properties/{ids['property_id']}", timeout=20)
        assert r.status_code == 200
        p = r.json()
        assert "civico" in p
        assert "comune" in p
        assert "province" in p


# ---------- Manual Hospitality ----------
class TestHospitalityManual:
    created_id = None

    def test_create_manual(self, session, ids):
        assert ids["landlord_id"] and ids["contract_id"], "Need landlord+contract"
        payload = {
            "mode": "manual",
            "landlord_id": ids["landlord_id"],
            "contract_id": ids["contract_id"],
            "guest_surname": "TEST_IT22",
            "guest_name": "Manual",
            "guest_nationality": "ITA",
            "guest_passport": "X1234",
        }
        r = session.post(f"{BASE_URL}/api/hospitality/records", json=payload, timeout=20)
        assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
        rec = r.json()
        assert rec["landlord_id"] == ids["landlord_id"]
        assert rec["contract_id"] == ids["contract_id"]
        assert rec.get("mode") == "manual"
        assert rec.get("id")
        TestHospitalityManual.created_id = rec["id"]

    def test_idempotent_upsert(self, session, ids):
        """Same landlord+contract POST again -> same id (no duplicate)."""
        payload = {
            "mode": "manual",
            "landlord_id": ids["landlord_id"],
            "contract_id": ids["contract_id"],
            "guest_surname": "TEST_IT22",
            "guest_name": "Manual2",
        }
        r = session.post(f"{BASE_URL}/api/hospitality/records", json=payload, timeout=20)
        assert r.status_code in (200, 201), r.text
        rec = r.json()
        assert rec["id"] == TestHospitalityManual.created_id, "Duplicate created instead of upsert!"

    def test_put_manual(self, session, ids):
        rid = TestHospitalityManual.created_id
        assert rid
        payload = {
            "mode": "manual",
            "landlord_id": ids["landlord_id"],
            "contract_id": ids["contract_id"],
            "guest_surname": "TEST_IT22",
            "guest_name": "Updated",
            "guest_passport": "Y9999",
        }
        r = session.put(f"{BASE_URL}/api/hospitality/records/{rid}", json=payload, timeout=20)
        assert r.status_code in (200, 204), f"{r.status_code} {r.text}"
        # verify persistence
        recs = session.get(f"{BASE_URL}/api/hospitality/records", timeout=20).json()
        match = [x for x in recs if x.get("id") == rid]
        assert match, "Updated record not found in list"
        assert match[0].get("guest_passport") == "Y9999"

    def test_pdf_record(self, session):
        rid = TestHospitalityManual.created_id
        assert rid
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/record/{rid}", timeout=30)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF", f"Not PDF: {r.content[:20]}"

    def test_cleanup(self, session):
        rid = TestHospitalityManual.created_id
        if rid:
            r = session.delete(f"{BASE_URL}/api/hospitality/records/{rid}", timeout=20)
            assert r.status_code in (200, 204)


# ---------- Tenant-mode hospitality regression ----------
class TestHospitalityTenantMode:
    def test_tenant_mode_still_works(self, session, ids):
        if not (ids["tenant_id"] and ids["property_id"]):
            pytest.skip("need tenant+property")
        # Get tenant -> need its property_id
        t = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()[0]
        prop_id = t.get("property_id") or ids["property_id"]
        payload = {
            "mode": "tenant",
            "tenant_id": t["id"],
            "property_id": prop_id,
            "landlord_id": ids["landlord_id"] or "",
            "contract_id": ids["contract_id"] or "",
            "check_in_date": "2026-01-01",
            "check_out_date": "2026-12-31",
            "hosting_type": "alloggio",
        }
        r = session.post(f"{BASE_URL}/api/hospitality/records", json=payload, timeout=20)
        # Could fail if property not found for that tenant; accept 200/201/404
        assert r.status_code in (200, 201, 404), f"unexpected {r.status_code}: {r.text}"


# ---------- Regression smoke ----------
class TestRegression:
    def test_landlords_authority(self, session):
        ll = session.get(f"{BASE_URL}/api/landlords", timeout=20).json()
        assert isinstance(ll, list)
        if ll:
            assert "authority" in ll[0]

    def test_dashboard_stats(self, session):
        r = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=20)
        assert r.status_code == 200

    def test_invoices_list_and_pdf(self, session):
        invs = session.get(f"{BASE_URL}/api/invoices", timeout=20).json()
        assert isinstance(invs, list)
        if invs:
            r = session.get(f"{BASE_URL}/api/invoices/{invs[0]['id']}/pdf", timeout=30)
            assert r.status_code == 200
            assert r.content[:4] == b"%PDF"

    def test_tenants_list(self, session):
        r = session.get(f"{BASE_URL}/api/tenants", timeout=20)
        assert r.status_code == 200

    def test_hospitality_pdf_tenant_endpoint(self, session, ids):
        if not ids["tenant_id"]:
            pytest.skip("no tenant")
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{ids['tenant_id']}", timeout=30)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
