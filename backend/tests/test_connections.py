"""Tests for Pagamenti <-> Inquilini <-> Proprieta connections (iteration 5)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    # Login
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "test"},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


# --- Tenants endpoint ---
class TestTenantsEnrichment:
    def test_get_tenants_returns_property_and_room(self, client):
        r = client.get(f"{BASE_URL}/api/tenants", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            t = data[0]
            # Required enriched fields must exist (even if empty)
            assert "property_address" in t, "property_address missing from tenant response"
            assert "room_number" in t, "room_number missing from tenant response"
            assert "payment_status" in t
            assert t["payment_status"] in ("paid", "not_paid")


# --- Properties endpoint ---
class TestPropertiesEnrichment:
    def test_get_properties_has_room_counts(self, client):
        r = client.get(f"{BASE_URL}/api/properties", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            p = data[0]
            assert "total_rooms_count" in p
            assert "occupied_rooms_count" in p
            assert "vacant_rooms_count" in p
            assert isinstance(p["total_rooms_count"], int)
            assert p["total_rooms_count"] == p["occupied_rooms_count"] + p["vacant_rooms_count"]

    def test_get_property_detail_has_rooms_array(self, client):
        r = client.get(f"{BASE_URL}/api/properties", timeout=30)
        assert r.status_code == 200
        props = r.json()
        if not props:
            pytest.skip("No properties")
        pid = props[0]["id"]
        r2 = client.get(f"{BASE_URL}/api/properties/{pid}", timeout=30)
        assert r2.status_code == 200
        detail = r2.json()
        assert "rooms" in detail
        assert isinstance(detail["rooms"], list)
        for room in detail["rooms"]:
            assert "tenant_name" in room


# --- Payments overview ---
class TestPaymentsOverview:
    def test_overview_groups_by_property(self, client):
        r = client.get(f"{BASE_URL}/api/payments/overview", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            p = data[0]
            for k in ("id", "address", "total_rooms", "paid_count", "not_paid_count", "rooms"):
                assert k in p, f"Missing key {k}"


# --- Payment creation flow ---
class TestPaymentCreation:
    def test_create_payment_with_any_tenant(self, client):
        tr = client.get(f"{BASE_URL}/api/tenants", timeout=30)
        assert tr.status_code == 200
        tenants = tr.json()
        if not tenants:
            pytest.skip("No tenants to test payment")
        tenant = tenants[0]
        payload = {
            "tenant_id": tenant["id"],
            "invoice_id": "",
            "amount": 1.0,
            "payment_method": "contanti",
            "payment_date": "2026-01-15",
            "notes": f"TEST_connection_{uuid.uuid4().hex[:6]}",
        }
        r = client.post(f"{BASE_URL}/api/payments", json=payload, timeout=30)
        assert r.status_code in (200, 201), f"POST /payments failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["tenant_id"] == tenant["id"]
        assert data["amount"] == 1.0

        # Verify GET /payments now includes it
        pg = client.get(f"{BASE_URL}/api/payments", timeout=30)
        assert pg.status_code == 200
        ids = [p.get("id") for p in pg.json()]
        assert data["id"] in ids

        # Cleanup: remove that payment directly via delete if endpoint exists (optional)

    def test_create_payment_invalid_tenant(self, client):
        payload = {
            "tenant_id": "non-existent-id-xyz",
            "invoice_id": "",
            "amount": 10,
            "payment_method": "contanti",
            "payment_date": "2026-01-15",
            "notes": "TEST_invalid",
        }
        r = client.post(f"{BASE_URL}/api/payments", json=payload, timeout=30)
        assert r.status_code == 404
