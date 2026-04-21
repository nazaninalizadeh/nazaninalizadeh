"""Iteration 6 tests - Ospitalita, Payments enrichment, Sconosciuto fix."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "test"},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


# --- Auth ---
class TestAuth:
    def test_login_and_me(self, client):
        r = client.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("email") == ADMIN_EMAIL


# --- Tenants enriched with property/room/payment_status ---
class TestTenantsEnrichment:
    def test_get_tenants_enriched(self, client):
        r = client.get(f"{BASE_URL}/api/tenants", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected at least 1 tenant in seed data"
        for t in data:
            assert "property_address" in t
            assert "room_number" in t
            assert "payment_status" in t
            assert t["payment_status"] in ("paid", "not_paid")
            assert "full_name" in t


# --- Payments endpoint enrichment: tenant_name, property_address, room_number ---
class TestPaymentsEnrichment:
    def test_get_payments_has_enriched_fields(self, client):
        r = client.get(f"{BASE_URL}/api/payments", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for p in data:
            # All three enrichment fields must be present (even if empty string)
            assert "tenant_name" in p, f"tenant_name missing in payment {p.get('id')}"
            assert "property_address" in p
            assert "room_number" in p
            # No Sconosciuto string should appear from backend
            assert p.get("tenant_name") != "Sconosciuto"

    def test_payments_no_orphaned_unknown(self, client):
        """Verify: no payment with empty tenant_id AND a non-empty tenant_name (fixed Sconosciuto bug)."""
        r = client.get(f"{BASE_URL}/api/payments", timeout=30)
        assert r.status_code == 200
        for p in r.json():
            if not p.get("tenant_id"):
                # Orphan: should have empty tenant_name, not Sconosciuto
                assert p.get("tenant_name", "") == ""

    def test_payments_overview_grouping(self, client):
        r = client.get(f"{BASE_URL}/api/payments/overview", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for prop in data:
            for k in ("id", "address", "total_rooms", "paid_count", "not_paid_count", "rooms"):
                assert k in prop


# --- Payment creation validates tenant exists ---
class TestPaymentValidation:
    def test_create_payment_invalid_tenant_returns_404(self, client):
        payload = {
            "tenant_id": "does-not-exist-xyz-" + uuid.uuid4().hex[:6],
            "invoice_id": "",
            "amount": 10.0,
            "payment_method": "contanti",
            "payment_date": "2026-01-15",
            "notes": "TEST_invalid_tenant",
        }
        r = client.post(f"{BASE_URL}/api/payments", json=payload, timeout=30)
        assert r.status_code == 404

    def test_create_payment_happy_path(self, client):
        tr = client.get(f"{BASE_URL}/api/tenants", timeout=30)
        tenants = tr.json()
        if not tenants:
            pytest.skip("No tenants")
        tenant = tenants[0]
        payload = {
            "tenant_id": tenant["id"],
            "invoice_id": "",
            "amount": 1.0,
            "payment_method": "contanti",
            "payment_date": "2026-01-15",
            "notes": f"TEST_iter6_{uuid.uuid4().hex[:6]}",
        }
        r = client.post(f"{BASE_URL}/api/payments", json=payload, timeout=30)
        assert r.status_code in (200, 201)
        pay = r.json()
        assert pay["tenant_id"] == tenant["id"]
        # Enriched fields expected when GET-ing
        g = client.get(f"{BASE_URL}/api/payments", timeout=30)
        found = [p for p in g.json() if p.get("id") == pay["id"]]
        assert len(found) == 1
        assert found[0]["tenant_name"] == tenant["full_name"]


# --- Hospitality PDF ---
class TestHospitalityPdf:
    def test_hospitality_pdf_happy_path(self, client):
        tr = client.get(f"{BASE_URL}/api/tenants", timeout=30)
        tenants = tr.json()
        if not tenants:
            pytest.skip("No tenants")
        tenant = tenants[0]
        r = client.get(f"{BASE_URL}/api/hospitality/pdf/{tenant['id']}", timeout=30)
        assert r.status_code == 200, f"PDF failed: {r.status_code} {r.text[:200]}"
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", "Response does not look like a PDF"
        assert len(r.content) > 500

    def test_hospitality_pdf_invalid_tenant_404(self, client):
        r = client.get(f"{BASE_URL}/api/hospitality/pdf/does-not-exist-xyz", timeout=30)
        assert r.status_code == 404


# --- Dashboard ---
class TestDashboard:
    def test_dashboard_stats_ok(self, client):
        r = client.get(f"{BASE_URL}/api/dashboard/stats", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
