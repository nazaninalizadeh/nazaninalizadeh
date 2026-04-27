"""
Iteration 11 tests:
- POST /api/auth/login (single-admin: invalidates other sessions)
- GET /api/auth/session-check returns valid:true
- GET /api/notifications/count
- GET /api/payment-calendar/{tenant_id} returns due_day from contract
- PUT /api/payment-calendar/{tenant_id}/{year}/{month} with paid + payment_method, not_paid, late
"""
import os
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"
CAPTCHA = "test_token_bypass_recaptcha"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": CAPTCHA
    })
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["email"].lower() == ADMIN_EMAIL.lower()
    assert "access_token" in s.cookies
    return s


@pytest.fixture(scope="module")
def tenant_with_room(session):
    r = session.get(f"{BASE_URL}/api/tenants")
    assert r.status_code == 200
    tenants = r.json()
    occupied = [t for t in tenants if t.get("room_id")]
    if not occupied:
        pytest.skip("No tenant with room_id available")
    return occupied[0]


# ============ Authentication ============
class TestAuth:
    def test_login_returns_200(self, session):
        # session fixture already exercised login
        r = session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        assert r.json()["email"].lower() == ADMIN_EMAIL.lower()

    def test_session_check_valid(self, session):
        r = session.get(f"{BASE_URL}/api/auth/session-check")
        assert r.status_code == 200
        data = r.json()
        assert data.get("valid") is True
        assert data.get("email", "").lower() == ADMIN_EMAIL.lower()

    def test_zz_session_check_unauth(self):
        r = requests.get(f"{BASE_URL}/api/auth/session-check")
        assert r.status_code == 401


# ============ Notifications count ============
class TestNotificationCount:
    def test_count_returns_number(self, session):
        r = session.get(f"{BASE_URL}/api/notifications/count")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 0

    def test_count_unauth(self):
        r = requests.get(f"{BASE_URL}/api/notifications/count")
        assert r.status_code == 401


# ============ Payment Calendar ============
class TestPaymentCalendar:
    def test_get_calendar_has_due_day(self, session, tenant_with_room):
        r = session.get(f"{BASE_URL}/api/payment-calendar/{tenant_with_room['id']}?year=2026")
        assert r.status_code == 200
        data = r.json()
        assert data["tenant_id"] == tenant_with_room["id"]
        assert data["year"] == 2026
        assert "due_day" in data
        assert isinstance(data["due_day"], int)
        assert 1 <= data["due_day"] <= 31
        assert len(data["calendar"]) == 12
        for m in data["calendar"]:
            assert m["month"] in range(1, 13)
            assert m["status"] in ("paid", "not_paid", "late", "none")

    def test_put_paid_with_payment_method(self, session, tenant_with_room):
        tid = tenant_with_room["id"]
        r = session.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/4",
            json={"status": "paid", "amount": 500, "payment_method": "contanti", "payment_date": "2026-04-05"},
        )
        assert r.status_code == 200, r.text
        # Verify persistence
        g = session.get(f"{BASE_URL}/api/payment-calendar/{tid}?year=2026")
        assert g.status_code == 200
        m4 = next(x for x in g.json()["calendar"] if x["month"] == 4)
        assert m4["status"] == "paid"
        assert m4["amount"] == 500
        assert m4["payment_method"] == "contanti"
        assert m4["manual_override"] is True

    def test_put_not_paid(self, session, tenant_with_room):
        tid = tenant_with_room["id"]
        r = session.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/4",
            json={"status": "not_paid"},
        )
        assert r.status_code == 200
        g = session.get(f"{BASE_URL}/api/payment-calendar/{tid}?year=2026")
        m4 = next(x for x in g.json()["calendar"] if x["month"] == 4)
        assert m4["status"] == "not_paid"

    def test_put_late(self, session, tenant_with_room):
        tid = tenant_with_room["id"]
        r = session.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/4",
            json={"status": "late"},
        )
        assert r.status_code == 200
        g = session.get(f"{BASE_URL}/api/payment-calendar/{tid}?year=2026")
        m4 = next(x for x in g.json()["calendar"] if x["month"] == 4)
        assert m4["status"] == "late"

    def test_put_invalid_status(self, session, tenant_with_room):
        tid = tenant_with_room["id"]
        r = session.put(
            f"{BASE_URL}/api/payment-calendar/{tid}/2026/4",
            json={"status": "wrong_status"},
        )
        assert r.status_code == 400

    def test_cleanup_override(self, session, tenant_with_room):
        tid = tenant_with_room["id"]
        r = session.delete(f"{BASE_URL}/api/payment-calendar/{tid}/2026/4")
        assert r.status_code == 200


# ============ Late tenants ============
class TestLateTenants:
    def test_late_tenants_endpoint(self, session):
        r = session.get(f"{BASE_URL}/api/late-tenants")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ============ Single-admin kick (runs LAST since it invalidates session fixture) ============
class TestZZSingleAdminKick:
    def test_login_invalidates_other_sessions(self, session):
        """Single-admin: when one admin logs in, all other active sessions are killed."""
        s2 = requests.Session()
        r = s2.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nazaninalizade890@gmail.com", "password": "1234@Admin", "captcha_token": CAPTCHA
        })
        assert r.status_code == 200, f"Admin2 login failed: {r.text}"

        rcheck = session.get(f"{BASE_URL}/api/auth/session-check")
        assert rcheck.status_code == 401, f"Expected admin1 to be kicked, got {rcheck.status_code}"

        r2 = s2.get(f"{BASE_URL}/api/auth/session-check")
        assert r2.status_code == 200

        s1 = requests.Session()
        r = s1.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": CAPTCHA
        })
        assert r.status_code == 200

        r2 = s2.get(f"{BASE_URL}/api/auth/session-check")
        assert r2.status_code == 401, f"Expected admin2 to be kicked, got {r2.status_code}"
