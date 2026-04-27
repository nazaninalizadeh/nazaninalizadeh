"""Iteration 14 tests:
- Dashboard tenants_late count == len(late_details) consistency
- Notifications mark-seen + count zero/non-zero behavior
- Hospitality PDF content and structure
- Tenant document upload returns /api/uploads/ prefix and downloads succeed
- Migration of legacy /uploads/ URLs in DB
- Property/Room image upload URL prefix
- Email service mocked + error fallback (no raise)
- Reminder check endpoint
"""
import os
import io
import asyncio
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://property-ops-16.preview.emergentagent.com").rstrip("/")
ADMIN2_EMAIL = "nazaninalizade890@gmail.com"
ADMIN2_PASSWORD = "1234@Admin"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN2_EMAIL,
        "password": ADMIN2_PASSWORD,
        "captcha_token": "",
    }, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Auth failed: {r.status_code} {r.text}")
    return s


# ============ Dashboard ============
class TestDashboardConsistency:
    def test_tenants_late_equals_late_details_length(self, session):
        for _ in range(3):
            r = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=20)
            assert r.status_code == 200
            data = r.json()
            assert "tenants_late" in data
            assert "late_details" in data
            assert isinstance(data["late_details"], list)
            assert data["tenants_late"] == len(data["late_details"]), \
                f"Mismatch: tenants_late={data['tenants_late']} vs len(late_details)={len(data['late_details'])}"

    def test_consistency_after_status_toggle(self, session):
        # Find one occupied tenant
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()
        occ = [t for t in tenants if t.get("room_id")]
        if not occ:
            pytest.skip("No occupied tenants to toggle")
        tenant = occ[0]
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        y, m = now.year, now.month
        # Toggle to late
        r = session.put(
            f"{BASE_URL}/api/payment-calendar/{tenant['id']}/{y}/{m}",
            json={"status": "late"}, timeout=20
        )
        assert r.status_code in (200, 201), f"toggle failed: {r.status_code} {r.text}"
        # Verify
        stats = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=20).json()
        assert stats["tenants_late"] == len(stats["late_details"])
        # Toggle to paid
        session.put(
            f"{BASE_URL}/api/payment-calendar/{tenant['id']}/{y}/{m}",
            json={"status": "paid"}, timeout=20
        )
        stats2 = session.get(f"{BASE_URL}/api/dashboard/stats", timeout=20).json()
        assert stats2["tenants_late"] == len(stats2["late_details"])


# ============ Notifications ============
class TestNotificationBadge:
    def test_count_endpoint(self, session):
        r = session.get(f"{BASE_URL}/api/notifications/count", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "count" in d
        assert isinstance(d["count"], int)

    def test_mark_seen_zeros_count(self, session):
        # Mark seen
        r = session.post(f"{BASE_URL}/api/notifications/mark-seen", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert "viewed_at" in d
        # Immediately count should be 0 because last_viewed_at >= became_late times for all current late
        r2 = session.get(f"{BASE_URL}/api/notifications/count", timeout=20)
        assert r2.status_code == 200
        assert r2.json()["count"] == 0


# ============ Hospitality PDF ============
class TestHospitalityPDF:
    def test_pdf_contains_required_strings(self, session):
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()
        if not tenants:
            pytest.skip("no tenants")
        tid = tenants[0]["id"]
        r = session.get(f"{BASE_URL}/api/hospitality/pdf/{tid}", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF"
        # Extract text
        try:
            from pypdf import PdfReader
        except Exception:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except Exception:
                pytest.skip("no pdf reader installed")
        reader = PdfReader(io.BytesIO(r.content))
        text = "".join((p.extract_text() or "") for p in reader.pages)
        # Be lenient about accented chars (PDF extraction may strip diacritics)
        required_substrings = [
            "COMUNICAZIONE DI OSPITALIT",  # 'À' may or may not extract
            "IN FAVORE DI CITTADINO EXTRACOMUNITARIO",
            "ARTICOLO 7 DEL DECRETO LEGISLATIVO",
            "Il sottoscritto",
            "DICHIARA CHE DAL",
            "A TEMPO INDETERMINATO",
            "ha fornito",
            "ha ceduto",
            "Cittadinanza",
            "PASSAPORTO",
            "firma del dichiarante",
            "ALLEGATI",
            "COPIA DI UN DOCUMENTO DEL DICHIARANTE",
        ]
        missing = [s for s in required_substrings if s not in text]
        assert not missing, f"PDF missing strings: {missing}\n--- extracted ---\n{text[:800]}"


# ============ Document upload returns /api/uploads/ ============
class TestDocumentUpload:
    def test_upload_url_prefix_and_download(self, session):
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()
        if not tenants:
            pytest.skip("no tenants")
        owner_id = tenants[0]["id"]

        # Minimal PDF bytes
        pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
        files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
        data = {"owner_id": owner_id, "owner_type": "tenant", "doc_type": "TEST_iter14"}
        r = session.post(f"{BASE_URL}/api/documents/upload", files=files, data=data, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        url = body.get("url", "")
        assert url.startswith("/api/uploads/"), f"Got url={url}"

        # Download via full URL using same session (cookies attached)
        full = f"{BASE_URL}{url}"
        r2 = session.get(full, timeout=30, allow_redirects=False)
        assert r2.status_code == 200, f"status={r2.status_code} headers={dict(r2.headers)}"
        # Should NOT be HTML (Dashboard) — should be the actual file bytes
        ctype = r2.headers.get("content-type", "")
        assert "text/html" not in ctype, f"expected file, got HTML — Dashboard redirect bug. ctype={ctype}"
        assert r2.content.startswith(b"%PDF"), f"content does not start with %PDF: {r2.content[:40]}"

        # Cleanup
        try:
            session.delete(f"{BASE_URL}/api/documents/{body['id']}", timeout=10)
        except Exception:
            pass


# ============ DB Migration check ============
class TestUploadsMigration:
    def test_no_legacy_upload_urls_in_documents(self, session):
        # Probe via API: ALL documents should have /api/uploads/ prefix now
        tenants = session.get(f"{BASE_URL}/api/tenants", timeout=20).json()
        bad = []
        checked = 0
        for t in tenants[:25]:
            docs = session.get(f"{BASE_URL}/api/documents/{t['id']}", timeout=15).json()
            for d in docs:
                checked += 1
                u = d.get("url", "")
                if u.startswith("/uploads/"):
                    bad.append(u)
        # If checked>0 and any bad → fail
        assert not bad, f"Legacy /uploads/ URLs still present: {bad[:5]} (checked {checked})"


# ============ Email service ============
class TestEmailService:
    def test_send_email_mock_when_no_key(self):
        import sys
        sys.path.insert(0, "/app/backend")
        # Ensure key is empty (it is in .env)
        os.environ["RESEND_API_KEY"] = ""
        from services.email_service import send_email  # type: ignore
        result = asyncio.get_event_loop().run_until_complete(
            send_email("test@example.com", "TEST_iter14", "<b>hi</b>")
        )
        assert result["status"] == "mocked"

    def test_send_email_error_does_not_raise(self):
        import sys
        sys.path.insert(0, "/app/backend")
        os.environ["RESEND_API_KEY"] = "re_invalid_key_for_test"
        # Reload not strictly needed since key is read at call time
        from services.email_service import send_email  # type: ignore
        try:
            result = asyncio.get_event_loop().run_until_complete(
                send_email("test@example.com", "TEST_iter14_err", "<b>hi</b>")
            )
        finally:
            os.environ["RESEND_API_KEY"] = ""
        # status may be sent (if Resend treats it generously) or error — must NOT raise
        assert result["status"] in ("error", "sent", "mocked")


class TestReminderCheck:
    def test_reminder_endpoint(self, session):
        r = session.post(f"{BASE_URL}/api/reminders/check", timeout=60)
        assert r.status_code == 200
        assert "completato" in r.json().get("message", "").lower() or "message" in r.json()
