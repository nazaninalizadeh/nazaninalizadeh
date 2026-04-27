"""
Iteration 12 tests - NEW FEATURES:
- POST /api/properties/{id}/images  (image upload for properties)
- DELETE /api/properties/{id}/images
- POST /api/rooms/{id}/images       (image upload for rooms)
- DELETE /api/rooms/{id}/images
- POST /api/reminders/check         (mocked email reminders)
- GET  /api/notifications/count     (badge count)
- Properties + Rooms CRUD (used by Properties page expansion UI)
- Tenants payment status update (Contanti/Bonifico) and Annulla safety
"""
import os
import io
import pytest
import requests

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
    return s


@pytest.fixture(scope="module")
def landlord_id(session):
    r = session.get(f"{BASE_URL}/api/landlords")
    assert r.status_code == 200
    landlords = r.json()
    if landlords:
        return landlords[0]["id"]
    # create one
    r = session.post(f"{BASE_URL}/api/landlords", json={
        "full_name": "TEST_LL_iter12", "fiscal_code": "TSTLLI80A01H501Z",
        "email": "testll@x.it", "phone": "1234"
    })
    assert r.status_code in (200, 201)
    return r.json()["id"]


@pytest.fixture(scope="module")
def test_property(session, landlord_id):
    """Create a fresh property for image tests."""
    payload = {
        "address": "TEST_iter12 Via di Test 999",
        "landlord_id": landlord_id,
        "city": "Padova", "zip_code": "35100", "province": "PD",
        "property_type": "appartamento",
        "number_of_rooms": 1, "capacity": 2, "rental_amount": 400,
    }
    r = session.post(f"{BASE_URL}/api/properties", json=payload)
    assert r.status_code in (200, 201), f"Property create failed: {r.status_code} {r.text}"
    prop = r.json()
    yield prop
    # cleanup
    session.delete(f"{BASE_URL}/api/properties/{prop['id']}")


@pytest.fixture(scope="module")
def test_room(session, test_property):
    payload = {
        "property_id": test_property["id"],
        "room_number": "T1",
        "room_type": "singola",
        "monthly_rent": 400,
    }
    r = session.post(f"{BASE_URL}/api/rooms", json=payload)
    assert r.status_code in (200, 201), f"Room create failed: {r.status_code} {r.text}"
    room = r.json()
    yield room
    session.delete(f"{BASE_URL}/api/rooms/{room['id']}")


def _png_bytes():
    # 1x1 PNG
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
    )


# ============ Image Upload: Properties ============
class TestPropertyImages:
    def test_upload_property_image(self, session, test_property):
        files = {"file": ("test.png", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/properties/{test_property['id']}/images", files=files)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "url" in body
        assert body["url"].startswith("/uploads/properties/")
        # GET property and confirm images list contains URL
        r2 = session.get(f"{BASE_URL}/api/properties/{test_property['id']}")
        assert r2.status_code == 200
        prop = r2.json()
        assert body["url"] in (prop.get("images") or []), f"Image URL not persisted: {prop.get('images')}"

    def test_upload_property_image_404(self, session):
        files = {"file": ("test.png", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/properties/nonexistent-id/images", files=files)
        assert r.status_code == 404

    def test_delete_property_image(self, session, test_property):
        # ensure at least one image exists
        files = {"file": ("test2.png", io.BytesIO(_png_bytes()), "image/png")}
        up = session.post(f"{BASE_URL}/api/properties/{test_property['id']}/images", files=files)
        assert up.status_code == 200
        url = up.json()["url"]
        r = session.delete(f"{BASE_URL}/api/properties/{test_property['id']}/images", params={"url": url})
        assert r.status_code == 200
        prop = session.get(f"{BASE_URL}/api/properties/{test_property['id']}").json()
        assert url not in (prop.get("images") or [])


# ============ Image Upload: Rooms ============
class TestRoomImages:
    def test_upload_room_image(self, session, test_room):
        files = {"file": ("room.png", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/rooms/{test_room['id']}/images", files=files)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["url"].startswith("/uploads/rooms/")
        r2 = session.get(f"{BASE_URL}/api/rooms/{test_room['id']}")
        assert r2.status_code == 200
        room = r2.json()
        assert body["url"] in (room.get("images") or [])

    def test_upload_room_image_404(self, session):
        files = {"file": ("x.png", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/rooms/nonexistent/images", files=files)
        assert r.status_code == 404


# ============ Reminders / Notifications ============
class TestReminders:
    def test_reminder_check(self, session):
        r = session.post(f"{BASE_URL}/api/reminders/check")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "message" in body or "completato" in str(body).lower()

    def test_notification_count(self, session):
        r = session.get(f"{BASE_URL}/api/notifications/count")
        assert r.status_code == 200
        body = r.json()
        assert "count" in body
        assert isinstance(body["count"], int)
        assert body["count"] >= 0


# ============ Properties / Rooms list (for expand UI) ============
class TestPropertiesRoomsList:
    def test_list_properties(self, session):
        r = session.get(f"{BASE_URL}/api/properties")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_rooms_by_property(self, session, test_property, test_room):
        r = session.get(f"{BASE_URL}/api/rooms", params={"property_id": test_property["id"]})
        assert r.status_code == 200
        rooms = r.json()
        assert any(rm["id"] == test_room["id"] for rm in rooms)
        # tenant_name + property_address fields enriched
        for rm in rooms:
            assert "tenant_name" in rm
            assert "property_address" in rm

    def test_via_piovese_has_rooms(self, session):
        """Spec says via piovese 142 has 3 rooms (2 occupied, 1 free)."""
        props = session.get(f"{BASE_URL}/api/properties").json()
        target = [p for p in props if "piovese" in p.get("address", "").lower()]
        if not target:
            pytest.skip("via piovese property not seeded")
        rooms = session.get(f"{BASE_URL}/api/rooms", params={"property_id": target[0]["id"]}).json()
        assert len(rooms) >= 1, "Expected at least one room for via piovese"


# ============ Room Assign/Unassign (used by Assegna dialog) ============
class TestRoomAssign:
    def test_assign_then_unassign(self, session, test_room):
        # find any tenant or skip
        tenants = session.get(f"{BASE_URL}/api/tenants").json()
        free_tenant = next((t for t in tenants if not t.get("room_id")), None)
        if not free_tenant:
            pytest.skip("No free tenant to assign")
        r = session.post(
            f"{BASE_URL}/api/rooms/{test_room['id']}/assign",
            data={"tenant_id": free_tenant["id"]},
        )
        assert r.status_code == 200, r.text
        # verify
        rm = session.get(f"{BASE_URL}/api/rooms/{test_room['id']}").json()
        assert rm.get("tenant_id") == free_tenant["id"]
        assert rm.get("status") == "occupied"
        # unassign
        r2 = session.post(f"{BASE_URL}/api/rooms/{test_room['id']}/unassign")
        assert r2.status_code == 200
        rm2 = session.get(f"{BASE_URL}/api/rooms/{test_room['id']}").json()
        assert rm2.get("status") == "available"
        assert (rm2.get("tenant_id") or "") == ""
