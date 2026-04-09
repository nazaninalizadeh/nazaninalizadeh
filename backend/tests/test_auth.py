"""
Backend API Tests for Property Management Auth System
- 2-step login flow (email+password+captcha → OTP verification)
- Single-device session enforcement
- Brute force protection
- Activity logging
"""

import pytest
import requests
import os
import time
import re
import subprocess

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from .env
ADMIN1_EMAIL = "alborz.sbd@gmail.com"
ADMIN1_PASSWORD = "Xk9mP2vLq7nWR!z"
ADMIN2_EMAIL = "nazaninalizade890@gmail.com"
ADMIN2_PASSWORD = "Hj5tF8yNb3cQZ!w"


def get_otp_from_logs():
    """Extract the latest OTP from backend logs"""
    try:
        result = subprocess.run(
            ["grep", "Codice OTP", "/var/log/supervisor/backend.err.log"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if lines:
            last_line = lines[-1]
            # Extract 6-digit OTP
            match = re.search(r'(\d{6})', last_line)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error getting OTP: {e}")
    return None


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestLoginStep1:
    """Test POST /api/auth/login-step1"""
    
    def test_login_step1_valid_credentials(self, api_client):
        """Valid admin credentials should return login_session_id"""
        response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "login_session_id" in data, "Response should contain login_session_id"
        assert "message" in data, "Response should contain message"
        assert len(data["login_session_id"]) > 0, "login_session_id should not be empty"
        print(f"✓ Login step 1 successful, session_id: {data['login_session_id'][:8]}...")
    
    def test_login_step1_non_whitelisted_email(self, api_client):
        """Non-whitelisted email should return 403"""
        response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": "notwhitelisted@example.com",
            "password": "somepassword",
            "captcha_token": ""
        })
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Non-whitelisted email rejected with 403: {data['detail']}")
    
    def test_login_step1_wrong_password(self, api_client):
        """Wrong password should return 401"""
        response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": "wrongpassword123",
            "captcha_token": ""
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Wrong password rejected with 401: {data['detail']}")
    
    def test_login_step1_invalid_email_format(self, api_client):
        """Invalid email format should return 422"""
        response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": "notanemail",
            "password": "somepassword",
            "captcha_token": ""
        })
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print("✓ Invalid email format rejected with 422")


class TestOTPVerification:
    """Test POST /api/auth/verify-otp"""
    
    def test_verify_otp_valid(self, api_client):
        """Valid OTP should return user data and set cookies"""
        # Step 1: Get login_session_id
        step1_response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        assert step1_response.status_code == 200
        login_session_id = step1_response.json()["login_session_id"]
        
        # Wait for OTP to be logged
        time.sleep(0.5)
        
        # Get OTP from logs
        otp = get_otp_from_logs()
        assert otp is not None, "Could not retrieve OTP from logs"
        print(f"Retrieved OTP: {otp}")
        
        # Step 2: Verify OTP
        step2_response = api_client.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id,
            "otp_code": otp
        })
        
        assert step2_response.status_code == 200, f"Expected 200, got {step2_response.status_code}: {step2_response.text}"
        data = step2_response.json()
        
        # Verify user data
        assert "id" in data, "Response should contain user id"
        assert "email" in data, "Response should contain email"
        assert data["email"] == ADMIN1_EMAIL
        assert "role" in data
        
        # Verify cookies are set
        cookies = step2_response.cookies
        assert "access_token" in cookies or "access_token" in api_client.cookies, "access_token cookie should be set"
        
        print(f"✓ OTP verification successful, user: {data['email']}, role: {data['role']}")
    
    def test_verify_otp_invalid_code(self, api_client):
        """Invalid OTP should return 400"""
        # Step 1: Get login_session_id
        step1_response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        assert step1_response.status_code == 200
        login_session_id = step1_response.json()["login_session_id"]
        
        # Step 2: Try invalid OTP
        step2_response = api_client.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id,
            "otp_code": "000000"  # Wrong OTP
        })
        
        assert step2_response.status_code == 400, f"Expected 400, got {step2_response.status_code}: {step2_response.text}"
        print(f"✓ Invalid OTP rejected with 400: {step2_response.json().get('detail')}")
    
    def test_verify_otp_invalid_session(self, api_client):
        """Invalid session ID should return 400"""
        response = api_client.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": "invalid-session-id-12345",
            "otp_code": "123456"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ Invalid session rejected with 400: {response.json().get('detail')}")


class TestAuthenticatedEndpoints:
    """Test authenticated endpoints"""
    
    def get_authenticated_session(self, api_client):
        """Helper to get an authenticated session"""
        # Step 1
        step1_response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        if step1_response.status_code != 200:
            return None
        login_session_id = step1_response.json()["login_session_id"]
        
        time.sleep(0.5)
        otp = get_otp_from_logs()
        if not otp:
            return None
        
        # Step 2
        step2_response = api_client.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id,
            "otp_code": otp
        })
        if step2_response.status_code != 200:
            return None
        
        return api_client
    
    def test_get_me_authenticated(self, api_client):
        """GET /api/auth/me with valid session should return user"""
        auth_client = self.get_authenticated_session(api_client)
        assert auth_client is not None, "Failed to authenticate"
        
        response = auth_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "email" in data
        assert data["email"] == ADMIN1_EMAIL
        print(f"✓ GET /api/auth/me returned user: {data['email']}")
    
    def test_get_me_unauthenticated(self, api_client):
        """GET /api/auth/me without session should return 401"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("✓ GET /api/auth/me without auth returns 401")
    
    def test_logout(self, api_client):
        """POST /api/auth/logout should invalidate session"""
        auth_client = self.get_authenticated_session(api_client)
        assert auth_client is not None, "Failed to authenticate"
        
        # Logout
        logout_response = auth_client.post(f"{BASE_URL}/api/auth/logout")
        assert logout_response.status_code == 200, f"Expected 200, got {logout_response.status_code}"
        
        # Verify session is invalidated
        me_response = auth_client.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 401, f"Expected 401 after logout, got {me_response.status_code}"
        print("✓ Logout successfully invalidated session")
    
    def test_activity_logs(self, api_client):
        """GET /api/auth/activity-logs should return login events"""
        auth_client = self.get_authenticated_session(api_client)
        assert auth_client is not None, "Failed to authenticate"
        
        response = auth_client.get(f"{BASE_URL}/api/auth/activity-logs")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Activity logs should be a list"
        
        # Should have at least one login event
        if len(data) > 0:
            log = data[0]
            assert "action" in log
            assert "admin_email" in log
            assert "timestamp" in log
            print(f"✓ Activity logs returned {len(data)} entries")
        else:
            print("✓ Activity logs endpoint works (empty list)")


class TestSingleDeviceEnforcement:
    """Test single-device session enforcement"""
    
    def test_new_login_invalidates_previous_session(self):
        """New login should invalidate previous session"""
        session1 = requests.Session()
        session2 = requests.Session()
        
        # Login with session 1
        step1_resp = session1.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        assert step1_resp.status_code == 200
        login_session_id_1 = step1_resp.json()["login_session_id"]
        
        time.sleep(0.5)
        otp1 = get_otp_from_logs()
        assert otp1 is not None
        
        step2_resp = session1.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id_1,
            "otp_code": otp1
        })
        assert step2_resp.status_code == 200
        
        # Verify session 1 works
        me_resp1 = session1.get(f"{BASE_URL}/api/auth/me")
        assert me_resp1.status_code == 200, "Session 1 should be valid"
        
        # Login with session 2 (same user)
        step1_resp2 = session2.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        assert step1_resp2.status_code == 200
        login_session_id_2 = step1_resp2.json()["login_session_id"]
        
        time.sleep(0.5)
        otp2 = get_otp_from_logs()
        assert otp2 is not None
        
        step2_resp2 = session2.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id_2,
            "otp_code": otp2
        })
        assert step2_resp2.status_code == 200
        
        # Session 2 should work
        me_resp2 = session2.get(f"{BASE_URL}/api/auth/me")
        assert me_resp2.status_code == 200, "Session 2 should be valid"
        
        # Session 1 should be invalidated
        me_resp1_after = session1.get(f"{BASE_URL}/api/auth/me")
        assert me_resp1_after.status_code == 401, f"Session 1 should be invalidated after new login, got {me_resp1_after.status_code}"
        
        print("✓ Single-device enforcement: new login invalidated previous session")


class TestBruteForceProtection:
    """Test brute force protection"""
    
    def test_account_lockout_after_failed_attempts(self, api_client):
        """Account should be locked after 5 failed attempts"""
        # Use a unique email to avoid affecting other tests
        test_email = ADMIN2_EMAIL
        
        # Make 5 failed login attempts
        for i in range(5):
            response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
                "email": test_email,
                "password": f"wrongpassword{i}",
                "captcha_token": ""
            })
            # Should get 401 for wrong password
            if response.status_code == 429:
                print(f"✓ Account locked after {i+1} attempts")
                return
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        # 6th attempt should be blocked
        response = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": test_email,
            "password": "wrongpassword6",
            "captcha_token": ""
        })
        
        assert response.status_code == 429, f"Expected 429 (locked), got {response.status_code}: {response.text}"
        print("✓ Brute force protection: account locked after 5 failed attempts")


class TestChangePassword:
    """Test POST /api/auth/change-password"""
    
    def test_change_password_wrong_current(self, api_client):
        """Wrong current password should return 400"""
        # First authenticate
        step1_resp = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        assert step1_resp.status_code == 200
        login_session_id = step1_resp.json()["login_session_id"]
        
        time.sleep(0.5)
        otp = get_otp_from_logs()
        assert otp is not None
        
        step2_resp = api_client.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id,
            "otp_code": otp
        })
        assert step2_resp.status_code == 200
        
        # Try to change password with wrong current password
        response = api_client.post(f"{BASE_URL}/api/auth/change-password", json={
            "current_password": "wrongcurrentpassword",
            "new_password": "NewPassword123!"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Change password with wrong current password rejected")
    
    def test_change_password_too_short(self, api_client):
        """New password too short should return 400"""
        # First authenticate
        step1_resp = api_client.post(f"{BASE_URL}/api/auth/login-step1", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD,
            "captcha_token": ""
        })
        assert step1_resp.status_code == 200
        login_session_id = step1_resp.json()["login_session_id"]
        
        time.sleep(0.5)
        otp = get_otp_from_logs()
        assert otp is not None
        
        step2_resp = api_client.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "login_session_id": login_session_id,
            "otp_code": otp
        })
        assert step2_resp.status_code == 200
        
        # Try to change password with too short new password
        response = api_client.post(f"{BASE_URL}/api/auth/change-password", json={
            "current_password": ADMIN1_PASSWORD,
            "new_password": "short"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Change password with too short new password rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
