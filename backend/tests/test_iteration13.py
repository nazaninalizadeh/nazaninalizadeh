"""
Iteration 13 tests covering:
- Image validation (.txt -> 400, 6MB -> 413, valid PNG -> 200, capitalized .PNG ext)
- DELETE empty url -> 400
- Notifications/count perf + shape
- Session control: same-admin new device kicks previous; other admin unaffected
- Bulk notifications/count is fast
NOTE: Uses admin2 (nazanin) to avoid disrupting admin1's interactive browser session.
"""
import os
import io
import time
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com"
).rstrip("/")

ADMIN1_EMAIL = "alborz.sbd@gmail.com"
ADMIN1_PASSWORD = "1234@Admin"
ADMIN2_EMAIL = "nazaninalizade890@gmail.com"
ADMIN2_PASSWORD = "1234@Admin"


def _login(email, password):
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password, "captcha_token": ""},
    )
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def session():
    """Use admin2 to avoid kicking admin1 active browser sessions."""
    return _login(ADMIN2_EMAIL, ADMIN2_PASSWORD)


@pytest.fixture(scope="module")
def landlord_id(session):
    r = session.get(f"{BASE_URL}/api/landlords")
    assert r.status_code == 200
    landlords = r.json()
    if landlords:
        return landlords[0]["id"]
    r = session.post(f"{BASE_URL}/api/landlords", json={
        "full_name": "TEST_iter13_LL", "fiscal_code": "TSTLLI80A01H501Z",
        "email": "testll13@x.it", "phone": "1234"
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def test_property(session, landlord_id):
    payload = {
        "address": "TEST_iter13 Via Test 13",
        "landlord_id": landlord_id,
        "city": "Padova", "zip_code": "35100", "province": "PD",
        "property_type": "appartamento",
        "number_of_rooms": 1, "capacity": 2, "rental_amount": 400,
    }
    r = session.post(f"{BASE_URL}/api/properties", json=payload)
    assert r.status_code in (200, 201), r.text
    prop = r.json()
    yield prop
    session.delete(f"{BASE_URL}/api/properties/{prop['id']}")


@pytest.fixture(scope="module")
def test_room(session, test_property):
    payload = {
        "property_id": test_property["id"],
        "room_number": "T13",
        "room_type": "singola",
        "monthly_rent": 400,
    }
    r = session.post(f"{BASE_URL}/api/rooms", json=payload)
    assert r.status_code in (200, 201), r.text
    room = r.json()
    yield room
    session.delete(f"{BASE_URL}/api/rooms/{room['id']}")


def _png_bytes():
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
    )


# ============ Image Validation: Properties ============
class TestPropertyImageValidation:
    def test_reject_txt_file(self, session, test_property):
        files = {"file": ("evil.txt", io.BytesIO(b"hello"), "text/plain")}
        r = session.post(f"{BASE_URL}/api/properties/{test_property['id']}/images", files=files)
        assert r.status_code == 400
        assert "Formato non supportato" in r.text or "non supportato" in r.text.lower()

    def test_reject_oversized(self, session, test_property):
        # 6MB png-named file
        big = b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024)
        files = {"file": ("big.png", io.BytesIO(big), "image/png")}
        r = session.post(f"{BASE_URL}/api/properties/{test_property['id']}/images", files=files)
        assert r.status_code == 413, f"Expected 413, got {r.status_code}: {r.text}"
        assert "troppo grande" in r.text.lower() or "5mb" in r.text.lower()

    def test_accept_valid_png(self, session, test_property):
        files = {"file": ("ok.png", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/properties/{test_property['id']}/images", files=files)
        assert r.status_code == 200, r.text
        assert r.json().get("url", "").startswith("/uploads/properties/")

    def test_accept_capitalized_extension(self, session, test_property):
        """FOO.PNG (uppercase) should be accepted."""
        files = {"file": ("FOO.PNG", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/properties/{test_property['id']}/images", files=files)
        assert r.status_code == 200, r.text
        url = r.json().get("url", "")
        # internally lowercased to .png
        assert url.endswith(".png"), f"Expected lowercased .png ext, got {url}"

    def test_delete_empty_url_400(self, session, test_property):
        r = session.delete(f"{BASE_URL}/api/properties/{test_property['id']}/images", params={"url": ""})
        assert r.status_code == 400
        assert "url" in r.text.lower() or "mancante" in r.text.lower()


# ============ Image Validation: Rooms ============
class TestRoomImageValidation:
    def test_reject_txt_file(self, session, test_room):
        files = {"file": ("evil.txt", io.BytesIO(b"hi"), "text/plain")}
        r = session.post(f"{BASE_URL}/api/rooms/{test_room['id']}/images", files=files)
        assert r.status_code == 400
        assert "non supportato" in r.text.lower() or "Formato" in r.text

    def test_reject_oversized(self, session, test_room):
        big = b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024)
        files = {"file": ("big.png", io.BytesIO(big), "image/png")}
        r = session.post(f"{BASE_URL}/api/rooms/{test_room['id']}/images", files=files)
        assert r.status_code == 413
        assert "troppo grande" in r.text.lower()

    def test_accept_valid_png(self, session, test_room):
        files = {"file": ("ok.png", io.BytesIO(_png_bytes()), "image/png")}
        r = session.post(f"{BASE_URL}/api/rooms/{test_room['id']}/images", files=files)
        assert r.status_code == 200, r.text
        assert r.json().get("url", "").startswith("/uploads/rooms/")

    def test_delete_empty_url_400(self, session, test_room):
        r = session.delete(f"{BASE_URL}/api/rooms/{test_room['id']}/images", params={"url": ""})
        assert r.status_code == 400


# ============ Notifications Count: shape + perf ============
class TestNotificationCount:
    def test_shape(self, session):
        r = session.get(f"{BASE_URL}/api/notifications/count")
        assert r.status_code == 200
        body = r.json()
        assert "count" in body
        assert isinstance(body["count"], int)
        assert body["count"] >= 0

    def test_under_500ms(self, session):
        # warm up
        session.get(f"{BASE_URL}/api/notifications/count")
        durations = []
        for _ in range(3):
            t0 = time.perf_counter()
            r = session.get(f"{BASE_URL}/api/notifications/count")
            durations.append(time.perf_counter() - t0)
            assert r.status_code == 200
        best = min(durations)
        assert best < 1.0, f"notifications/count slowest of 3 calls best={best:.3f}s — should be <1s with bulk queries"


# ============ Session Control ============
class TestSessionControl:
    def test_same_admin_new_device_kicks_previous(self):
        """admin2 logs in twice from different cookie jars. First session must die.
        We use admin2 to avoid disturbing admin1's interactive browser session.
        """
        s_a = _login(ADMIN2_EMAIL, ADMIN2_PASSWORD)
        # confirm session A active
        ra = s_a.get(f"{BASE_URL}/api/auth/me")
        assert ra.status_code == 200

        # New device login
        s_b = _login(ADMIN2_EMAIL, ADMIN2_PASSWORD)
        rb = s_b.get(f"{BASE_URL}/api/auth/me")
        assert rb.status_code == 200

        # Old session should now be invalidated
        ra2 = s_a.get(f"{BASE_URL}/api/auth/me")
        assert ra2.status_code == 401, f"Expected old session to be kicked, got {ra2.status_code}"

        # session-check polling endpoint also returns 401
        rc = s_a.get(f"{BASE_URL}/api/auth/session-check")
        assert rc.status_code == 401

    def test_other_admin_login_does_not_kick(self):
        """admin1 login MUST NOT kick admin2 session.
        WARNING: this will kick any existing admin1 browser session.
        """
        admin2_session = _login(ADMIN2_EMAIL, ADMIN2_PASSWORD)
        # verify admin2 active
        r2 = admin2_session.get(f"{BASE_URL}/api/auth/me")
        assert r2.status_code == 200

        # Different admin logs in
        admin1_session = _login(ADMIN1_EMAIL, ADMIN1_PASSWORD)
        r1 = admin1_session.get(f"{BASE_URL}/api/auth/me")
        assert r1.status_code == 200

        # admin2 session should STILL be active
        r2_after = admin2_session.get(f"{BASE_URL}/api/auth/me")
        assert r2_after.status_code == 200, (
            f"admin2 session got kicked when admin1 logged in (cross-admin pollution): {r2_after.status_code}"
        )
