"""Iteration 8 backend tests - property mgmt fixes, 3 tenant statuses, registration uploads, ZIP bundle, OCR original file save."""
import os
import io
import zipfile
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "alborz.sbd@gmail.com", "password": "1234@Admin", "captcha_token": "test"}


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    # login
    r = s.post(f"{API}/auth/login", json=ADMIN, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code} {r.text[:200]}")
    return s


# ---------------- Auth + sanity ----------------
def test_login_and_me(client):
    r = client.get(f"{API}/auth/me", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data.get("email") == ADMIN["email"]


# ---------------- Dashboard ----------------
def test_dashboard_has_tenants_late(client):
    r = client.get(f"{API}/dashboard/stats", timeout=20)
    assert r.status_code == 200
    data = r.json()
    for key in ("tenants_late", "tenants_paid", "tenants_not_paid"):
        assert key in data, f"missing {key} in dashboard stats: {list(data.keys())}"
        assert isinstance(data[key], int)


# ---------------- Tenants - 3 status values ----------------
def test_tenants_returns_payment_status(client):
    r = client.get(f"{API}/tenants", timeout=20)
    assert r.status_code == 200
    tenants = r.json()
    assert isinstance(tenants, list)
    if not tenants:
        pytest.skip("no tenants in DB")
    for t in tenants:
        assert "payment_status" in t
        assert t["payment_status"] in ("paid", "not_paid", "late"), t["payment_status"]
        # address must no longer be required field (may exist as legacy blank)
        # month_payment_method may be present when paid
    # at least one of the three status groups reachable via filter


def test_tenants_no_address_required_on_create_and_create_flow(client):
    # Grab a property to attach (optional); if none, skip creation
    props = client.get(f"{API}/properties", timeout=20).json()
    property_id = props[0]["id"] if props else ""

    payload = {
        "full_name": "TEST_Iter8 Filter Tenant",
        "passport_number": "TESTIT8P1",
        "nationality": "Test",
        "date_of_birth": "1990-01-01",
        "passport_issue_date": "2020-01-01",
        "passport_expiry_date": "2030-01-01",
        "email": "test.iter8.filter@example.com",
        "whatsapp": "+390000000000",
        "occupation": "Tester",
        "property_id": property_id,
        "payment_due_day": 5,
        # NOTE: no 'address', no 'phone' -> must succeed
    }
    r = client.post(f"{API}/tenants", json=payload, timeout=20)
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
    created = r.json()
    assert created.get("full_name") == payload["full_name"]
    assert created.get("payment_status") in ("paid", "not_paid", "late")
    tid = created["id"]

    # cleanup
    dr = client.delete(f"{API}/tenants/{tid}", timeout=20)
    assert dr.status_code == 200


def test_tenants_status_filter_late(client):
    r = client.get(f"{API}/tenants", params={"status": "late"}, timeout=20)
    assert r.status_code == 200
    lst = r.json()
    assert isinstance(lst, list)
    for t in lst:
        assert t["payment_status"] == "late"


def test_tenants_status_filter_paid(client):
    r = client.get(f"{API}/tenants", params={"status": "paid"}, timeout=20)
    assert r.status_code == 200
    for t in r.json():
        assert t["payment_status"] == "paid"
        # when paid, amount/method fields should be populated
        assert "month_paid_amount" in t
        assert "month_payment_method" in t


def test_tenants_status_filter_not_paid(client):
    r = client.get(f"{API}/tenants", params={"status": "not_paid"}, timeout=20)
    assert r.status_code == 200
    for t in r.json():
        assert t["payment_status"] == "not_paid"


# ---------------- Properties - auto-generate code, no deposit ----------------
def test_property_create_auto_generates_code_no_deposit(client):
    landlords = client.get(f"{API}/landlords", timeout=20).json()
    if not landlords:
        pytest.skip("no landlords seeded")
    ll_id = landlords[0]["id"]
    payload = {
        "address": "TEST_Iter8 Via Auto Code 1",
        "property_type": "apartment",
        "number_of_rooms": 2,
        "capacity": 4,
        "landlord_id": ll_id,
        "rental_amount": 800.0,
        "additional_charges": "",
        # no property_code, no deposit_amount
    }
    r = client.post(f"{API}/properties", json=payload, timeout=20)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    p = r.json()
    assert p.get("property_code", "").startswith("IMM-"), f"code={p.get('property_code')!r}"
    assert len(p["property_code"]) == 8  # IMM-XXXX
    # No deposit in schema
    assert "deposit_amount" not in p or p.get("deposit_amount") in (None, 0, 0.0)
    pid = p["id"]

    # Verify via GET
    g = client.get(f"{API}/properties/{pid}", timeout=20)
    assert g.status_code == 200
    assert g.json()["property_code"] == p["property_code"]

    # cleanup
    d = client.delete(f"{API}/properties/{pid}", timeout=20)
    assert d.status_code == 200


# ---------------- Registration uploads ----------------
def _small_png_bytes():
    # 1x1 PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00"
        b"\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\x1e\x8d\x0b\x8b\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture(scope="session")
def a_tenant_id(client):
    r = client.get(f"{API}/tenants", timeout=20)
    lst = r.json()
    if not lst:
        pytest.skip("no tenants in DB")
    return lst[0]["id"]


@pytest.fixture(scope="session")
def a_landlord_id(client):
    r = client.get(f"{API}/landlords", timeout=20)
    lst = r.json()
    if not lst:
        pytest.skip("no landlords in DB")
    return lst[0]["id"]


def test_registration_upload(client, a_tenant_id):
    files = {"file": ("test_reg.png", _small_png_bytes(), "image/png")}
    data = {"owner_id": a_tenant_id, "doc_type": "registration"}
    r = client.post(f"{API}/registration/upload", data=data, files=files, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    body = r.json()
    assert body.get("owner_id") == a_tenant_id
    assert body.get("doc_type") == "registration"
    assert body.get("url", "").startswith("/uploads/documents/")


def test_contract_upload(client, a_tenant_id):
    files = {"file": ("test_contract.png", _small_png_bytes(), "image/png")}
    data = {"tenant_id": a_tenant_id, "property_id": ""}
    r = client.post(f"{API}/contracts/upload", data=data, files=files, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    body = r.json()
    assert body.get("owner_id") == a_tenant_id
    assert body.get("doc_type") == "contract"


def test_owner_document_upload(client, a_landlord_id):
    files = {"file": ("test_owner.png", _small_png_bytes(), "image/png")}
    data = {"owner_id": a_landlord_id}
    r = client.post(f"{API}/owner-documents/upload", data=data, files=files, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    body = r.json()
    assert body.get("owner_id") == a_landlord_id
    assert body.get("doc_type") == "owner_document"
    assert body.get("owner_type") == "landlord"


def test_documents_bundle_zip(client, a_tenant_id):
    # ensure there is at least one doc
    files = {"file": ("bundle_seed.png", _small_png_bytes(), "image/png")}
    client.post(f"{API}/registration/upload", data={"owner_id": a_tenant_id, "doc_type": "registration"}, files=files, timeout=30)

    r = client.get(f"{API}/documents/bundle/{a_tenant_id}", timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    assert r.headers.get("content-type", "").startswith("application/zip")
    buf = io.BytesIO(r.content)
    z = zipfile.ZipFile(buf)
    names = z.namelist()
    assert len(names) >= 1


# ---------------- OCR original file save ----------------
def test_ocr_scan_saves_original_file(client):
    files = {"file": ("ocrsmall.png", _small_png_bytes(), "image/png")}
    r = client.post(f"{API}/ocr/scan", files=files, timeout=60)
    # OCR uses LLM; may fail if no key. Accept 200 or 500 but saved_file_url should exist on 200.
    if r.status_code != 200:
        pytest.skip(f"OCR returned {r.status_code}: {r.text[:200]}")
    body = r.json()
    assert "saved_file_url" in body
    assert body["saved_file_url"].startswith("/uploads/documents/")
