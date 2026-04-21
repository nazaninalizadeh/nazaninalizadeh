"""
Property Management System - Comprehensive Backend Tests
Tests: Auth, Landlords, Properties, Rooms, Tenants, Invoices, Payments, Reports, Notifications
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from .env
ADMIN_EMAIL = "alborz.sbd@gmail.com"
ADMIN_PASSWORD = "1234@Admin"


class TestSession:
    """Shared session with auth cookies"""
    session = None
    
    @classmethod
    def get_session(cls):
        if cls.session is None:
            cls.session = requests.Session()
            cls.session.headers.update({"Content-Type": "application/json"})
        return cls.session


@pytest.fixture(scope="module")
def auth_session():
    """Authenticate and return session with cookies"""
    session = TestSession.get_session()
    
    # Login
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "captcha_token": ""
    })
    
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    return session


# ============ AUTH TESTS ============
class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "captcha_token": ""
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["email"] == ADMIN_EMAIL
        assert "name" in data
        assert "role" in data
        print(f"Login success: {data['email']} ({data['role']})")
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword",
            "captcha_token": ""
        })
        assert response.status_code == 401
        print("Wrong password correctly rejected")
    
    def test_login_non_whitelisted(self):
        """Test login with non-whitelisted email"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "notallowed@example.com",
            "password": "anypassword",
            "captcha_token": ""
        })
        assert response.status_code == 403
        print("Non-whitelisted email correctly rejected")
    
    def test_get_me_authenticated(self, auth_session):
        """Test /me endpoint with valid session"""
        response = auth_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"Authenticated user: {data['email']}")
    
    def test_get_me_unauthenticated(self):
        """Test /me endpoint without auth"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Unauthenticated /me correctly rejected")


# ============ DASHBOARD TESTS ============
class TestDashboard:
    """Dashboard stats endpoint tests"""
    
    def test_dashboard_stats(self, auth_session):
        """Test dashboard stats returns all required fields"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        required_fields = [
            "total_tenants", "total_landlords", "total_properties",
            "total_rooms", "occupied_rooms", "vacant_rooms",
            "active_contracts", "unpaid_invoices",
            "total_monthly_income", "total_deposits",
            "total_collected", "total_outstanding",
            "recent_payments", "overdue_invoices"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Dashboard stats: {data['total_tenants']} tenants, {data['total_rooms']} rooms")


# ============ LANDLORD TESTS ============
class TestLandlords:
    """Landlord CRUD tests"""
    created_landlord_id = None
    
    def test_create_landlord(self, auth_session):
        """Create a landlord with Codice Fiscale"""
        payload = {
            "full_name": f"TEST_Landlord_{uuid.uuid4().hex[:6]}",
            "codice_fiscale": "RSSMRA85M01H501Z",
            "phone": "+39 333 1234567",
            "email": f"test_landlord_{uuid.uuid4().hex[:6]}@example.com",
            "whatsapp": "+39 333 1234567",
            "id_type": "Carta d'identita",
            "id_number": "CA12345AB",
            "bank_details": "IT60X0542811101000000123456",
            "notes": "Test landlord"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/landlords", json=payload)
        assert response.status_code == 200, f"Create landlord failed: {response.text}"
        
        data = response.json()
        assert data["full_name"] == payload["full_name"]
        assert data["codice_fiscale"] == payload["codice_fiscale"]
        assert "id" in data
        
        TestLandlords.created_landlord_id = data["id"]
        print(f"Created landlord: {data['full_name']} (ID: {data['id']})")
    
    def test_get_landlords_list(self, auth_session):
        """Get landlords list with occupancy columns"""
        response = auth_session.get(f"{BASE_URL}/api/landlords")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            landlord = data[0]
            # Check occupancy fields
            assert "properties_count" in landlord
            assert "total_rooms" in landlord
            assert "occupied_rooms" in landlord
            assert "vacant_rooms" in landlord
            print(f"Landlords list: {len(data)} landlords")
    
    def test_get_landlord_detail(self, auth_session):
        """Get single landlord with properties"""
        if not TestLandlords.created_landlord_id:
            pytest.skip("No landlord created")
        
        response = auth_session.get(f"{BASE_URL}/api/landlords/{TestLandlords.created_landlord_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TestLandlords.created_landlord_id
        assert "properties" in data
        print(f"Landlord detail: {data['full_name']}")


# ============ PROPERTY TESTS ============
class TestProperties:
    """Property CRUD tests"""
    created_property_id = None
    
    def test_create_property(self, auth_session):
        """Create a property linked to landlord"""
        if not TestLandlords.created_landlord_id:
            pytest.skip("No landlord created")
        
        payload = {
            "property_code": f"PROP-{uuid.uuid4().hex[:6].upper()}",
            "address": "Via Test 123, Roma",
            "property_type": "Appartamento",
            "number_of_rooms": 3,
            "capacity": 4,
            "landlord_id": TestLandlords.created_landlord_id,
            "rental_amount": 1200.00,
            "deposit_amount": 2400.00,
            "additional_charges": "Utenze escluse"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/properties", json=payload)
        assert response.status_code == 200, f"Create property failed: {response.text}"
        
        data = response.json()
        assert data["property_code"] == payload["property_code"]
        assert data["landlord_id"] == TestLandlords.created_landlord_id
        assert "id" in data
        
        TestProperties.created_property_id = data["id"]
        print(f"Created property: {data['property_code']} (ID: {data['id']})")
    
    def test_get_properties_list(self, auth_session):
        """Get properties list with occupancy status"""
        response = auth_session.get(f"{BASE_URL}/api/properties")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            prop = data[0]
            assert "occupancy_status" in prop
            assert "current_tenants_count" in prop
            print(f"Properties list: {len(data)} properties")


# ============ ROOM TESTS ============
class TestRooms:
    """Room CRUD and assignment tests"""
    created_room_id = None
    
    def test_create_room_single(self, auth_session):
        """Create a single room in property"""
        if not TestProperties.created_property_id:
            pytest.skip("No property created")
        
        payload = {
            "property_id": TestProperties.created_property_id,
            "room_number": f"R{uuid.uuid4().hex[:3].upper()}",
            "room_type": "single",
            "floor": "1",
            "monthly_rent": 450.00,
            "description": "Test single room",
            "bill_responsible": ""
        }
        
        response = auth_session.post(f"{BASE_URL}/api/rooms", json=payload)
        assert response.status_code == 200, f"Create room failed: {response.text}"
        
        data = response.json()
        assert data["room_number"] == payload["room_number"]
        assert data["room_type"] == "single"
        assert data["status"] == "available"
        assert "id" in data
        
        TestRooms.created_room_id = data["id"]
        print(f"Created room: {data['room_number']} ({data['room_type']})")
    
    def test_create_room_double(self, auth_session):
        """Create a double room"""
        if not TestProperties.created_property_id:
            pytest.skip("No property created")
        
        payload = {
            "property_id": TestProperties.created_property_id,
            "room_number": f"D{uuid.uuid4().hex[:3].upper()}",
            "room_type": "double",
            "floor": "2",
            "monthly_rent": 650.00,
            "description": "Test double room",
            "bill_responsible": ""
        }
        
        response = auth_session.post(f"{BASE_URL}/api/rooms", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["room_type"] == "double"
        print(f"Created double room: {data['room_number']}")
    
    def test_get_rooms_list(self, auth_session):
        """Get rooms list with status and tenant info"""
        response = auth_session.get(f"{BASE_URL}/api/rooms")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            room = data[0]
            assert "status" in room
            assert "tenant_name" in room
            assert "property_address" in room
            print(f"Rooms list: {len(data)} rooms")
    
    def test_get_rooms_by_property(self, auth_session):
        """Get rooms filtered by property"""
        if not TestProperties.created_property_id:
            pytest.skip("No property created")
        
        response = auth_session.get(f"{BASE_URL}/api/rooms?property_id={TestProperties.created_property_id}")
        assert response.status_code == 200
        
        data = response.json()
        for room in data:
            assert room["property_id"] == TestProperties.created_property_id
        print(f"Rooms in property: {len(data)}")


# ============ TENANT TESTS ============
class TestTenants:
    """Tenant CRUD tests with Codice Fiscale and room assignment"""
    created_tenant_id = None
    
    def test_create_tenant(self, auth_session):
        """Create tenant with Codice Fiscale and property/room assignment"""
        payload = {
            "full_name": f"TEST_Tenant_{uuid.uuid4().hex[:6]}",
            "codice_fiscale": "BNCLRA90A01H501X",
            "passport_number": f"AA{uuid.uuid4().hex[:6].upper()}",
            "nationality": "Italiana",
            "date_of_birth": "1990-01-15",
            "passport_issue_date": "2020-01-01",
            "passport_expiry_date": "2030-01-01",
            "id_type": "Carta d'identita",
            "id_number": "CA98765XY",
            "phone": "+39 333 9876543",
            "email": f"test_tenant_{uuid.uuid4().hex[:6]}@example.com",
            "whatsapp": "+39 333 9876543",
            "address": "Via Tenant 456, Milano",
            "occupation": "Ingegnere",
            "notes": "Test tenant",
            "deposit_amount": 900.00,
            "property_id": TestProperties.created_property_id or "",
            "room_id": TestRooms.created_room_id or ""
        }
        
        response = auth_session.post(f"{BASE_URL}/api/tenants", json=payload)
        assert response.status_code == 200, f"Create tenant failed: {response.text}"
        
        data = response.json()
        assert data["full_name"] == payload["full_name"]
        assert data["codice_fiscale"] == payload["codice_fiscale"]
        assert "id" in data
        assert "remaining_balance" in data
        assert "total_paid" in data
        assert "total_due" in data
        
        TestTenants.created_tenant_id = data["id"]
        print(f"Created tenant: {data['full_name']} (ID: {data['id']})")
    
    def test_get_tenants_list(self, auth_session):
        """Get tenants list with balance columns"""
        response = auth_session.get(f"{BASE_URL}/api/tenants")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            tenant = data[0]
            # Check required fields for frontend table (codice_fiscale may be empty for old records)
            assert "remaining_balance" in tenant
            assert "room_number" in tenant
            assert "property_address" in tenant
            print(f"Tenants list: {len(data)} tenants")
    
    def test_get_tenant_detail(self, auth_session):
        """Get tenant detail with payments, documents, balance"""
        if not TestTenants.created_tenant_id:
            pytest.skip("No tenant created")
        
        response = auth_session.get(f"{BASE_URL}/api/tenants/{TestTenants.created_tenant_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TestTenants.created_tenant_id
        assert "documents" in data
        assert "payments" in data
        assert "invoices" in data
        assert "contracts" in data
        assert "remaining_balance" in data
        print(f"Tenant detail: {data['full_name']}")


# ============ ROOM ASSIGNMENT TESTS ============
class TestRoomAssignment:
    """Room assignment and unassignment tests"""
    
    def test_assign_tenant_to_room(self, auth_session):
        """Assign tenant to room via POST /rooms/{id}/assign"""
        if not TestRooms.created_room_id or not TestTenants.created_tenant_id:
            pytest.skip("No room or tenant created")
        
        # Use form data for assignment
        response = auth_session.post(
            f"{BASE_URL}/api/rooms/{TestRooms.created_room_id}/assign",
            data={"tenant_id": TestTenants.created_tenant_id},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200, f"Assign failed: {response.text}"
        
        # Verify room status changed
        room_response = auth_session.get(f"{BASE_URL}/api/rooms/{TestRooms.created_room_id}")
        room_data = room_response.json()
        assert room_data["status"] == "occupied"
        assert room_data["tenant_id"] == TestTenants.created_tenant_id
        print(f"Assigned tenant to room: {room_data['room_number']}")
    
    def test_unassign_tenant_from_room(self, auth_session):
        """Unassign tenant from room"""
        if not TestRooms.created_room_id:
            pytest.skip("No room created")
        
        response = auth_session.post(f"{BASE_URL}/api/rooms/{TestRooms.created_room_id}/unassign")
        assert response.status_code == 200
        
        # Verify room status changed back
        room_response = auth_session.get(f"{BASE_URL}/api/rooms/{TestRooms.created_room_id}")
        room_data = room_response.json()
        assert room_data["status"] == "available"
        print(f"Unassigned tenant from room: {room_data['room_number']}")


# ============ CONTRACT TESTS ============
class TestContracts:
    """Contract CRUD tests"""
    created_contract_id = None
    
    def test_create_contract(self, auth_session):
        """Create a contract for tenant"""
        if not TestTenants.created_tenant_id or not TestProperties.created_property_id:
            pytest.skip("No tenant or property created")
        
        payload = {
            "tenant_id": TestTenants.created_tenant_id,
            "property_id": TestProperties.created_property_id,
            "room_id": TestRooms.created_room_id or "",
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "rent_amount": 450.00,
            "deposit_amount": 900.00,
            "terms": "Contratto di locazione standard"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/contracts", json=payload)
        assert response.status_code == 200, f"Create contract failed: {response.text}"
        
        data = response.json()
        assert "contract_number" in data
        assert data["status"] == "active"
        assert "id" in data
        
        TestContracts.created_contract_id = data["id"]
        print(f"Created contract: {data['contract_number']}")
    
    def test_get_contracts_list(self, auth_session):
        """Get contracts list"""
        response = auth_session.get(f"{BASE_URL}/api/contracts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Contracts list: {len(data)} contracts")


# ============ INVOICE TESTS ============
class TestInvoices:
    """Invoice CRUD tests"""
    created_invoice_id = None
    
    def test_create_invoice(self, auth_session):
        """Create an invoice for tenant"""
        if not TestTenants.created_tenant_id or not TestProperties.created_property_id or not TestContracts.created_contract_id:
            pytest.skip("Missing dependencies")
        
        payload = {
            "tenant_id": TestTenants.created_tenant_id,
            "property_id": TestProperties.created_property_id,
            "contract_id": TestContracts.created_contract_id,
            "invoice_type": "Affitto Mensile",
            "amount": 450.00,
            "due_date": "2026-02-01",
            "description": "Affitto Gennaio 2026"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/invoices", json=payload)
        assert response.status_code == 200, f"Create invoice failed: {response.text}"
        
        data = response.json()
        assert "invoice_number" in data
        assert data["payment_status"] == "unpaid"
        assert data["paid_amount"] == 0.0
        assert "id" in data
        
        TestInvoices.created_invoice_id = data["id"]
        print(f"Created invoice: {data['invoice_number']} - EUR {data['amount']}")
    
    def test_get_invoices_list(self, auth_session):
        """Get invoices list"""
        response = auth_session.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Invoices list: {len(data)} invoices")


# ============ PAYMENT TESTS ============
class TestPayments:
    """Payment tests including partial payments"""
    
    def test_create_partial_payment(self, auth_session):
        """Create a partial payment and verify balance updates"""
        if not TestTenants.created_tenant_id or not TestInvoices.created_invoice_id:
            pytest.skip("Missing dependencies")
        
        # Get tenant balance before payment
        tenant_before = auth_session.get(f"{BASE_URL}/api/tenants/{TestTenants.created_tenant_id}").json()
        total_paid_before = tenant_before.get("total_paid", 0)
        
        payload = {
            "tenant_id": TestTenants.created_tenant_id,
            "invoice_id": TestInvoices.created_invoice_id,
            "amount": 200.00,  # Partial payment
            "payment_method": "bonifico",
            "payment_date": "2026-01-15",
            "notes": "Pagamento parziale"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/payments", json=payload)
        assert response.status_code == 200, f"Create payment failed: {response.text}"
        
        data = response.json()
        assert data["amount"] == 200.00
        assert "id" in data
        
        # Verify tenant total_paid updated
        tenant_after = auth_session.get(f"{BASE_URL}/api/tenants/{TestTenants.created_tenant_id}").json()
        assert tenant_after["total_paid"] == total_paid_before + 200.00
        
        # Verify invoice status changed to partial
        invoice = auth_session.get(f"{BASE_URL}/api/invoices/{TestInvoices.created_invoice_id}").json()
        assert invoice["payment_status"] == "partial"
        assert invoice["paid_amount"] == 200.00
        
        print(f"Created partial payment: EUR {data['amount']}")
    
    def test_create_remaining_payment(self, auth_session):
        """Create remaining payment to complete invoice"""
        if not TestTenants.created_tenant_id or not TestInvoices.created_invoice_id:
            pytest.skip("Missing dependencies")
        
        payload = {
            "tenant_id": TestTenants.created_tenant_id,
            "invoice_id": TestInvoices.created_invoice_id,
            "amount": 250.00,  # Remaining amount
            "payment_method": "contanti",
            "payment_date": "2026-01-20",
            "notes": "Saldo"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/payments", json=payload)
        assert response.status_code == 200
        
        # Verify invoice status changed to paid
        invoice = auth_session.get(f"{BASE_URL}/api/invoices/{TestInvoices.created_invoice_id}").json()
        assert invoice["payment_status"] == "paid"
        assert invoice["paid_amount"] == 450.00
        
        print("Invoice fully paid")
    
    def test_get_payments_list(self, auth_session):
        """Get payments list with tenant names"""
        response = auth_session.get(f"{BASE_URL}/api/payments")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            payment = data[0]
            assert "tenant_name" in payment
            print(f"Payments list: {len(data)} payments")
    
    def test_get_tenant_payments(self, auth_session):
        """Get payments for specific tenant"""
        if not TestTenants.created_tenant_id:
            pytest.skip("No tenant created")
        
        response = auth_session.get(f"{BASE_URL}/api/payments/tenant/{TestTenants.created_tenant_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        for payment in data:
            assert payment["tenant_id"] == TestTenants.created_tenant_id
        print(f"Tenant payments: {len(data)}")


# ============ DOCUMENT UPLOAD TESTS ============
class TestDocuments:
    """Document upload tests"""
    created_doc_id = None
    
    def test_upload_document(self, auth_session):
        """Upload a document for tenant"""
        if not TestTenants.created_tenant_id:
            pytest.skip("No tenant created")
        
        # Create a small test file - use a fresh session for multipart
        import io
        files = {
            'file': ('test_document.txt', io.BytesIO(b'Test document content'), 'text/plain'),
            'owner_id': (None, TestTenants.created_tenant_id),
            'owner_type': (None, 'tenant'),
            'doc_type': (None, 'passport')
        }
        
        # Use a fresh session with cookies from auth_session
        upload_session = requests.Session()
        upload_session.cookies.update(auth_session.cookies)
        
        response = upload_session.post(
            f"{BASE_URL}/api/documents/upload",
            files=files
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        doc_data = response.json()
        assert "id" in doc_data
        assert doc_data["owner_id"] == TestTenants.created_tenant_id
        assert doc_data["doc_type"] == "passport"
        assert "url" in doc_data
        
        TestDocuments.created_doc_id = doc_data["id"]
        print(f"Uploaded document: {doc_data['filename']}")
    
    def test_get_documents(self, auth_session):
        """Get documents for owner"""
        if not TestTenants.created_tenant_id:
            pytest.skip("No tenant created")
        
        response = auth_session.get(f"{BASE_URL}/api/documents/{TestTenants.created_tenant_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Documents: {len(data)}")


# ============ REPORTS TESTS ============
class TestReports:
    """Report generation tests"""
    
    def test_generate_monthly_report(self, auth_session):
        """Generate monthly report with summary data"""
        response = auth_session.get(f"{BASE_URL}/api/reports/generate?report_type=monthly")
        assert response.status_code == 200, f"Report failed: {response.text}"
        
        data = response.json()
        assert data["report_type"] == "monthly"
        assert "summary" in data
        assert "tenant_balances" in data
        
        summary = data["summary"]
        required_summary_fields = [
            "total_payments_received", "payment_count",
            "unpaid_invoices", "partial_payments",
            "overdue_invoices", "total_overdue_amount",
            "total_rooms", "occupied_rooms", "vacant_rooms",
            "occupancy_rate"
        ]
        
        for field in required_summary_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        print(f"Monthly report: {summary['payment_count']} payments, {summary['occupancy_rate']}% occupancy")
    
    def test_generate_weekly_report(self, auth_session):
        """Generate weekly report"""
        response = auth_session.get(f"{BASE_URL}/api/reports/generate?report_type=weekly")
        assert response.status_code == 200
        
        data = response.json()
        assert data["report_type"] == "weekly"
        print("Weekly report generated")
    
    def test_generate_yearly_report(self, auth_session):
        """Generate yearly report"""
        response = auth_session.get(f"{BASE_URL}/api/reports/generate?report_type=yearly")
        assert response.status_code == 200
        
        data = response.json()
        assert data["report_type"] == "yearly"
        print("Yearly report generated")
    
    def test_download_report_pdf(self, auth_session):
        """Download report as PDF"""
        response = auth_session.get(f"{BASE_URL}/api/reports/pdf?report_type=monthly")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0
        print(f"PDF downloaded: {len(response.content)} bytes")


# ============ NOTIFICATIONS TESTS ============
class TestNotifications:
    """Notifications endpoint tests"""
    
    def test_get_notifications(self, auth_session):
        """Get notifications list"""
        response = auth_session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check notification structure if any exist
        if len(data) > 0:
            notification = data[0]
            assert "type" in notification
            assert "severity" in notification
            assert "title" in notification
            assert "message" in notification
        
        print(f"Notifications: {len(data)}")


# ============ CLEANUP TESTS ============
class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_document(self, auth_session):
        """Delete test document"""
        if TestDocuments.created_doc_id:
            response = auth_session.delete(f"{BASE_URL}/api/documents/{TestDocuments.created_doc_id}")
            assert response.status_code == 200
            print("Document deleted")
    
    def test_delete_tenant(self, auth_session):
        """Delete test tenant"""
        if TestTenants.created_tenant_id:
            response = auth_session.delete(f"{BASE_URL}/api/tenants/{TestTenants.created_tenant_id}")
            assert response.status_code == 200
            print("Tenant deleted")
    
    def test_delete_room(self, auth_session):
        """Delete test room"""
        if TestRooms.created_room_id:
            response = auth_session.delete(f"{BASE_URL}/api/rooms/{TestRooms.created_room_id}")
            assert response.status_code == 200
            print("Room deleted")
    
    def test_delete_property(self, auth_session):
        """Delete test property"""
        if TestProperties.created_property_id:
            response = auth_session.delete(f"{BASE_URL}/api/properties/{TestProperties.created_property_id}")
            assert response.status_code == 200
            print("Property deleted")
    
    def test_delete_landlord(self, auth_session):
        """Delete test landlord"""
        if TestLandlords.created_landlord_id:
            response = auth_session.delete(f"{BASE_URL}/api/landlords/{TestLandlords.created_landlord_id}")
            assert response.status_code == 200
            print("Landlord deleted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
