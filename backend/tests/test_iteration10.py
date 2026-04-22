"""
Iteration 10 - Monthly Payment Status System tests
Covers: editable monthly status, manual override PUT/DELETE, late-tenants endpoint,
dashboard late_details, notifications late_payment, tenants enrichment with overrides.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"
CAPTCHA = "test_token_bypass_recaptcha"


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": CAPTCHA},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def a_tenant(client):
    r = client.get(f"{BASE_URL}/api/tenants", timeout=30)
    assert r.status_code == 200
    tenants = r.json()
    # prefer one with a room so late-tenants/dashboard would see it
    with_room = [t for t in tenants if t.get("room_id")]
    chosen = with_room[0] if with_room else tenants[0]
    return chosen


# --- Payment Calendar GET ---
class TestPaymentCalendarGet:
    def test_returns_12_months(self, client, a_tenant):
        r = client.get(f"{BASE_URL}/api/payment-calendar/{a_tenant['id']}?year=2026", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["tenant_id"] == a_tenant["id"]
        assert data["year"] == 2026
        assert len(data["calendar"]) == 12
        first = data["calendar"][0]
        # required keys
        for k in ("month", "month_name", "year", "status", "amount", "manual_override"):
            assert k in first, f"Missing key {k} in calendar month"
        assert first["month"] == 1
        assert first["month_name"] == "Gennaio"
        assert data["calendar"][11]["month_name"] == "Dicembre"

    def test_invalid_tenant_404(self, client):
        r = client.get(f"{BASE_URL}/api/payment-calendar/non-existent-xyz", timeout=30)
        assert r.status_code == 404


# --- Payment Calendar PUT / DELETE (manual override) ---
class TestMonthlyOverride:
    def test_put_creates_override(self, client, a_tenant):
        tid = a_tenant["id"]
        # cleanup any previous override
        client.delete(f"{BASE_URL}/api/payment-calendar/{tid}/2026/4", timeout=30)

        payload = {"status": "paid", "amount": 500, "payment_method": "contanti", "notes": "TEST_iter10"}
        r = client.put(f"{BASE_URL}/api/payment-calendar/{tid}/2026/4", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "paid"
        assert body["month"] == 4
        assert body["year"] == 2026

        # GET back to verify manual_override is true and value persisted
        g = client.get(f"{BASE_URL}/api/payment-calendar/{tid}?year=2026", timeout=30)
        assert g.status_code == 200
        april = g.json()["calendar"][3]
        assert april["month"] == 4
        assert april["status"] == "paid"
        assert april["manual_override"] is True
        assert april["amount"] == 500

    def test_put_invalid_status_400(self, client, a_tenant):
        tid = a_tenant["id"]
        r = client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/5",
            json={"status": "bogus", "amount": 0},
            timeout=30,
        )
        assert r.status_code == 400

    def test_put_invalid_month_400(self, client, a_tenant):
        tid = a_tenant["id"]
        r = client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/13",
            json={"status": "paid"},
            timeout=30,
        )
        assert r.status_code == 400

    def test_put_late_status(self, client, a_tenant):
        tid = a_tenant["id"]
        client.delete(f"{BASE_URL}/api/payment-calendar/{tid}/2026/6", timeout=30)
        r = client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/6",
            json={"status": "late", "amount": 0, "notes": "TEST_iter10_late"},
            timeout=30,
        )
        assert r.status_code == 200
        g = client.get(f"{BASE_URL}/api/payment-calendar/{tid}?year=2026", timeout=30)
        june = g.json()["calendar"][5]
        assert june["status"] == "late"
        assert june["manual_override"] is True

    def test_delete_removes_override(self, client, a_tenant):
        tid = a_tenant["id"]
        # ensure override exists
        client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/4",
            json={"status": "paid", "amount": 500},
            timeout=30,
        )
        d = client.delete(f"{BASE_URL}/api/payment-calendar/{tid}/2026/4", timeout=30)
        assert d.status_code == 200

        # Verify override gone (manual_override false for that month)
        g = client.get(f"{BASE_URL}/api/payment-calendar/{tid}?year=2026", timeout=30)
        april = g.json()["calendar"][3]
        assert april["manual_override"] is False


# --- Late tenants endpoint ---
class TestLateTenants:
    def test_late_tenants_endpoint(self, client):
        r = client.get(f"{BASE_URL}/api/late-tenants", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # each item must carry expected fields
        if data:
            item = data[0]
            for k in ("tenant_id", "tenant_name", "property_address", "room_number", "month", "month_name", "year", "status"):
                assert k in item, f"Missing key {k} in late-tenants item"
            assert item["status"] == "late"

    def test_late_tenants_reflects_override(self, client, a_tenant):
        """Force current month to 'late' via override, confirm tenant appears."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        tid = a_tenant["id"]
        if not a_tenant.get("room_id"):
            pytest.skip("Tenant has no room; late-tenants only includes occupied tenants")

        # set override for current month -> late
        client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}",
            json={"status": "late", "amount": 0, "notes": "TEST_iter10_currentlate"},
            timeout=30,
        )
        try:
            r = client.get(f"{BASE_URL}/api/late-tenants", timeout=30)
            assert r.status_code == 200
            ids = [item["tenant_id"] for item in r.json()]
            assert tid in ids, "Tenant with override=late should appear in /api/late-tenants"
        finally:
            client.delete(f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}", timeout=30)


# --- Dashboard stats late_details ---
class TestDashboardLateDetails:
    def test_late_details_array(self, client):
        r = client.get(f"{BASE_URL}/api/dashboard/stats", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "late_details" in data
        assert isinstance(data["late_details"], list)
        assert "tenants_late" in data
        assert "tenants_paid" in data
        assert "tenants_not_paid" in data
        # late_details length should equal tenants_late
        assert len(data["late_details"]) == data["tenants_late"]
        if data["late_details"]:
            item = data["late_details"][0]
            for k in ("tenant_id", "tenant_name"):
                assert k in item


# --- Notifications ---
class TestNotifications:
    def test_notifications_includes_late_payment(self, client, a_tenant):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        tid = a_tenant["id"]
        if not a_tenant.get("room_id"):
            pytest.skip("Tenant has no room; notifications likely filter occupied tenants")

        # force current-month override => late
        client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}",
            json={"status": "late", "notes": "TEST_iter10_notif"},
            timeout=30,
        )
        try:
            r = client.get(f"{BASE_URL}/api/notifications", timeout=30)
            assert r.status_code == 200
            notifs = r.json()
            assert isinstance(notifs, list)
            types = {n.get("type") for n in notifs}
            assert "late_payment" in types, f"Expected 'late_payment' type in notifications, got: {types}"
            # the late_payment notification for our tenant
            matching = [n for n in notifs if n.get("type") == "late_payment" and n.get("tenant_id") == tid]
            assert matching, "Expected a late_payment notification for overridden tenant"
        finally:
            client.delete(f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}", timeout=30)


# --- Tenants list respects override ---
class TestTenantsOverride:
    def test_tenant_payment_status_reflects_override(self, client, a_tenant):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        tid = a_tenant["id"]

        # override paid
        client.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}",
            json={"status": "paid", "amount": 500, "notes": "TEST_iter10_paid"},
            timeout=30,
        )
        try:
            r = client.get(f"{BASE_URL}/api/tenants/{tid}", timeout=30)
            assert r.status_code == 200
            assert r.json().get("payment_status") == "paid"

            # flip override to late
            client.put(
                f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}",
                json={"status": "late"},
                timeout=30,
            )
            r2 = client.get(f"{BASE_URL}/api/tenants/{tid}", timeout=30)
            assert r2.status_code == 200
            assert r2.json().get("payment_status") == "late"
        finally:
            client.delete(f"{BASE_URL}/api/payment-calendar/{tid}/{now.year}/{now.month}", timeout=30)
