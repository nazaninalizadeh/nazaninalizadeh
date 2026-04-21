"""Simplified payment logic backend tests.
Covers:
- GET /api/tenants shape (payment_status, month_paid_amount, no remaining_balance/total_due)
- GET /api/tenants/{id} shape (deposit_amount, no negative numbers, no totals)
- POST /api/payments does NOT change tenant.total_paid
- GET /api/payments/overview grouped structure
- GET /api/dashboard/stats simplified keys
- GET /api/occupancy-overview uses current month
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "captcha_token": "",
    })
    if r.status_code != 200:
        pytest.skip(f"Login failed {r.status_code}: {r.text}")
    return s


@pytest.fixture(scope="module")
def seeded(session):
    """Create landlord->property->room->tenant, assign and register a current-month payment."""
    created = {}

    # Landlord
    ll = session.post(f"{BASE_URL}/api/landlords", json={
        "full_name": "TEST_LL_Simp",
        "codice_fiscale": f"TESTLL{uuid.uuid4().hex[:8].upper()}",
        "email": "test_ll_simp@example.com",
        "phone": "3331234567",
        "whatsapp": "3331234567",
        "id_number": f"ID{uuid.uuid4().hex[:8].upper()}",
        "address": "Via Test 1",
        "bank_details": "IBAN IT60X0542811101000000123456",
    })
    assert ll.status_code in (200, 201), ll.text
    created["landlord_id"] = ll.json()["id"]

    # Property
    prop = session.post(f"{BASE_URL}/api/properties", json={
        "landlord_id": created["landlord_id"],
        "landlord_name": "TEST_LL_Simp",
        "property_code": f"TEST_P{uuid.uuid4().hex[:6].upper()}",
        "address": "Via TestProp 2",
        "city": "Milano",
        "property_type": "apartment",
        "total_rooms": 2,
        "number_of_rooms": 2,
        "capacity": 4,
        "rental_amount": 1000,
        "deposit_amount": 1000,
    })
    assert prop.status_code in (200, 201), prop.text
    created["property_id"] = prop.json()["id"]

    # Room
    room = session.post(f"{BASE_URL}/api/rooms", json={
        "property_id": created["property_id"],
        "room_number": f"R{uuid.uuid4().hex[:4]}",
        "room_type": "single",
        "monthly_rent": 500,
        "size_sqm": 15,
    })
    assert room.status_code in (200, 201), room.text
    created["room_id"] = room.json()["id"]

    # Tenant
    tenant = session.post(f"{BASE_URL}/api/tenants", json={
        "full_name": "TEST_Tenant_Simp",
        "email": f"tenant_{uuid.uuid4().hex[:6]}@example.com",
        "phone": "3339876543",
        "whatsapp": "3339876543",
        "passport_number": f"P{uuid.uuid4().hex[:8].upper()}",
        "nationality": "IT",
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "place_of_birth": "Milano",
        "passport_issue_date": "2020-01-01",
        "passport_expiry_date": "2030-01-01",
        "address": "Via Tenant 3",
        "occupation": "dev",
        "codice_fiscale": f"RSSMRA90A01F205{uuid.uuid4().hex[:1].upper()}",
        "deposit_amount": 1000,
    })
    assert tenant.status_code in (200, 201), tenant.text
    created["tenant_id"] = tenant.json()["id"]

    # Assign
    a = session.post(
        f"{BASE_URL}/api/rooms/{created['room_id']}/assign",
        data={"tenant_id": created["tenant_id"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert a.status_code == 200, a.text

    # Current month payment
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p = session.post(f"{BASE_URL}/api/payments", json={
        "tenant_id": created["tenant_id"],
        "amount": 500,
        "payment_date": today,
        "payment_method": "contanti",
        "notes": "TEST payment",
    })
    assert p.status_code in (200, 201), p.text
    created["payment_id"] = p.json()["id"]

    yield created

    # Cleanup
    session.delete(f"{BASE_URL}/api/tenants/{created['tenant_id']}")
    session.delete(f"{BASE_URL}/api/rooms/{created['room_id']}")
    session.delete(f"{BASE_URL}/api/properties/{created['property_id']}")
    session.delete(f"{BASE_URL}/api/landlords/{created['landlord_id']}")


# ---------------- Tenants shape ----------------
class TestTenantsShape:
    def test_list_tenants_has_payment_status_no_totals(self, session):
        r = session.get(f"{BASE_URL}/api/tenants")
        assert r.status_code == 200, r.text
        tenants = r.json()
        assert isinstance(tenants, list)
        if not tenants:
            pytest.skip("No tenants to assert shape on")
        t = tenants[0]
        assert "payment_status" in t
        assert "month_paid_amount" in t
        assert t["payment_status"] in ("paid", "not_paid", "-")
        # Forbidden keys
        assert "remaining_balance" not in t, f"remaining_balance must not exist: {t}"
        assert "total_due" not in t, f"total_due must not exist: {t}"

    def test_get_tenant_detail_shape(self, session, seeded):
        r = session.get(f"{BASE_URL}/api/tenants/{seeded['tenant_id']}")
        assert r.status_code == 200, r.text
        t = r.json()
        assert t["payment_status"] == "paid"
        assert t["month_paid_amount"] == 500
        assert t["deposit_amount"] == 1000
        # No forbidden fields
        for k in ("remaining_balance", "total_due", "total_paid", "saldo"):
            assert k not in t, f"Forbidden key {k} in tenant: {t.keys()}"
        # No negative values
        for k, v in t.items():
            if isinstance(v, (int, float)):
                assert v >= 0, f"Negative value for {k}: {v}"


# ---------------- Payments ----------------
class TestPayments:
    def test_payment_does_not_update_tenant_total_paid(self, session, seeded):
        # After seeded payment, tenant must not carry a total_paid/remaining_balance field
        r = session.get(f"{BASE_URL}/api/tenants/{seeded['tenant_id']}")
        assert r.status_code == 200
        t = r.json()
        assert "total_paid" not in t
        assert "remaining_balance" not in t
        assert t["deposit_amount"] == 1000  # unchanged constant guarantee

    def test_payments_overview_grouped(self, session, seeded):
        r = session.get(f"{BASE_URL}/api/payments/overview")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # Find our property
        props = [p for p in data if p["id"] == seeded["property_id"]]
        assert props, "Seeded property not in overview"
        prop = props[0]
        assert "rooms" in prop
        assert prop["total_rooms"] >= 1
        # Find our room
        rooms = [rm for rm in prop["rooms"] if rm["id"] == seeded["room_id"]]
        assert rooms, "Seeded room not in overview"
        room = rooms[0]
        assert room["payment_status"] == "paid"
        assert room["payment_amount"] == 500
        assert room["tenant_id"] == seeded["tenant_id"]


# ---------------- Dashboard ----------------
class TestDashboard:
    def test_dashboard_stats_simplified(self, session, seeded):
        r = session.get(f"{BASE_URL}/api/dashboard/stats")
        assert r.status_code == 200, r.text
        d = r.json()
        for key in ("tenants_paid", "tenants_not_paid", "month_collected", "total_deposits"):
            assert key in d, f"Missing dashboard key: {key}"
        assert "total_outstanding" not in d, "total_outstanding must be removed"
        assert d["tenants_paid"] >= 1
        assert d["month_collected"] >= 500
        assert d["total_deposits"] >= 1000


# ---------------- Occupancy ----------------
class TestOccupancy:
    def test_occupancy_uses_current_month(self, session, seeded):
        r = session.get(f"{BASE_URL}/api/occupancy-overview")
        assert r.status_code == 200, r.text
        data = r.json()
        prop = next((p for p in data if p["id"] == seeded["property_id"]), None)
        assert prop is not None
        room = next((rm for rm in prop["rooms"] if rm["id"] == seeded["room_id"]), None)
        assert room is not None
        assert room["payment_status"] == "paid"
        assert room["payment_amount"] == 500
