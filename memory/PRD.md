# PropertyOps - Property Rental & Tenant Management System

## Product Requirement Document (PRD)

**Version:** 2.0 (Phase 2 Complete)  
**Last Updated:** January 2026  
**Status:** Phase 2 Complete

---

## 1. Executive Summary

PropertyOps is a comprehensive web-based property rental and tenant management system designed to streamline operations for property managers, landlords, and administrators. The platform provides end-to-end management of tenants, landlords, properties, rental contracts, invoices, and payments through a modern, secure, and scalable dashboard interface.

---

## 2. Tech Stack

### Frontend
- **Framework:** React 19.0
- **Routing:** React Router DOM 7.5
- **UI Library:** Shadcn/UI with Radix UI components
- **Styling:** Tailwind CSS 3.4
- **State Management:** React Context API
- **HTTP Client:** Axios
- **Fonts:** Outfit (headings), IBM Plex Sans (body), JetBrains Mono (code)
- **Icons:** Lucide React

### Backend
- **Framework:** FastAPI 0.110
- **Language:** Python 3.11
- **Database:** MongoDB (Motor async driver)
- **Authentication:** JWT with bcrypt password hashing
- **PDF Generation:** ReportLab
- **Email Service:** Resend
- **Environment:** Python-dotenv

### Design System
- **Theme:** Light mode with professional blue palette
- **Primary Color:** #1D4ED8 (Blue 700)
- **Background:** #F8FAFC (Slate 50)
- **Cards:** White (#FFFFFF) with slate borders
- **Typography:** Swiss & High-Contrast archetype

---

## 3. Database Schema

### Collections

#### 3.1 Users
```json
{
  "_id": "ObjectId",
  "email": "string (unique, indexed)",
  "password_hash": "string",
  "name": "string",
  "role": "string (super_admin|admin|operator|accountant|landlord)",
  "created_at": "ISO datetime"
}
```

#### 3.2 Tenants
```json
{
  "id": "UUID",
  "full_name": "string",
  "passport_number": "string (indexed)",
  "nationality": "string",
  "date_of_birth": "string",
  "passport_issue_date": "string",
  "passport_expiry_date": "string",
  "phone": "string",
  "email": "string",
  "whatsapp": "string",
  "address": "string",
  "occupation": "string",
  "notes": "string",
  "deposit_amount": "float",
  "total_paid": "float",
  "current_property": "string|null",
  "created_at": "ISO datetime",
  "created_by": "user_id"
}
```

#### 3.3 Landlords
```json
{
  "id": "UUID",
  "full_name": "string",
  "phone": "string",
  "email": "string",
  "whatsapp": "string",
  "id_number": "string",
  "bank_details": "string",
  "notes": "string",
  "created_at": "ISO datetime",
  "created_by": "user_id"
}
```

#### 3.4 Properties
```json
{
  "id": "UUID",
  "property_code": "string (indexed)",
  "address": "string",
  "property_type": "string",
  "number_of_rooms": "integer",
  "capacity": "integer",
  "landlord_id": "string",
  "landlord_name": "string",
  "rental_amount": "float",
  "deposit_amount": "float",
  "additional_charges": "string",
  "occupancy_status": "string (vacant|occupied)",
  "created_at": "ISO datetime",
  "created_by": "user_id"
}
```

#### 3.5 Contracts
```json
{
  "id": "UUID",
  "contract_number": "string (indexed, CNT-YYYYMMDD-XXXXXXXX)",
  "tenant_id": "string",
  "tenant_name": "string",
  "property_id": "string",
  "property_address": "string",
  "start_date": "string",
  "end_date": "string",
  "rent_amount": "float",
  "deposit_amount": "float",
  "terms": "string",
  "status": "string (active|expired|cancelled|renewed)",
  "created_at": "ISO datetime",
  "created_by": "user_id"
}
```

#### 3.6 Invoices
```json
{
  "id": "UUID",
  "invoice_number": "string (indexed, INV-YYYYMMDD-XXXXXXXX)",
  "tenant_id": "string",
  "tenant_name": "string",
  "property_id": "string",
  "property_address": "string",
  "contract_id": "string",
  "invoice_type": "string (rent|deposit|penalty|other)",
  "amount": "float",
  "issue_date": "ISO datetime",
  "due_date": "string",
  "payment_status": "string (paid|unpaid)",
  "description": "string",
  "created_at": "ISO datetime",
  "created_by": "user_id"
}
```

#### 3.7 Payments
```json
{
  "id": "UUID",
  "invoice_id": "string",
  "amount": "float",
  "payment_method": "string (cash|bank_transfer|check|credit_card)",
  "payment_date": "string",
  "created_at": "ISO datetime",
  "created_by": "user_id"
}
```

---

## 4. User Roles & Permissions

### 4.1 Super Admin
- Full system access
- User management
- All CRUD operations
- System configuration

### 4.2 Admin
- Manage tenants, landlords, properties
- Create contracts and invoices
- Record payments
- Generate reports

### 4.3 Operator
- View and manage tenants
- Create and update contracts
- Generate invoices
- Limited deletion rights

### 4.4 Accountant
- View financial data
- Manage invoices and payments
- Generate financial reports
- Read-only access to tenant/property data

### 4.5 Landlord (Future)
- View own properties
- View tenants in own properties
- View income reports
- Read-only access

---

## 5. MVP Features (Implemented)

### 5.1 Authentication & Security
- ✅ Email/password login with JWT tokens
- ✅ CAPTCHA integration (Google reCAPTCHA)
- ✅ Bcrypt password hashing
- ✅ HTTP-only cookie-based authentication
- ✅ Access token (30 min) + Refresh token (7 days)
- ✅ Role-based access control
- ✅ Protected routes

### 5.2 Tenant Management
- ✅ Create, read, update, delete tenants
- ✅ Comprehensive tenant profiles (passport, contact, occupation)
- ✅ Track deposit amounts and payments
- ✅ Link tenants to properties
- ✅ Search and filter tenants
- ✅ Tenant detail page with full history

### 5.3 Landlord Management
- ✅ Create, read, update, delete landlords
- ✅ Store contact and bank details
- ✅ Link landlords to properties
- ✅ View properties per landlord
- ✅ Landlord detail page with income summary

### 5.4 Property Management
- ✅ Create, read, update, delete properties
- ✅ Link properties to landlords
- ✅ Track occupancy status
- ✅ Monitor tenant count vs capacity
- ✅ Store rental and deposit amounts
- ✅ Search and filter properties

### 5.5 Contract Management
- ✅ Create rental contracts
- ✅ Auto-generate contract numbers
- ✅ Link contracts to tenants and properties
- ✅ Track contract status (active, expired, cancelled, renewed)
- ✅ Generate PDF contracts
- ✅ Download contracts
- ✅ Update contract status

### 5.6 Invoice Management
- ✅ Create invoices (rent, deposit, penalty, other)
- ✅ Auto-generate invoice numbers
- ✅ Link invoices to tenants, properties, and contracts
- ✅ Track payment status
- ✅ Generate PDF invoices
- ✅ Download invoices
- ✅ Record payments against invoices

### 5.7 Payment Management
- ✅ Record payments
- ✅ Multiple payment methods
- ✅ Auto-update invoice status
- ✅ Update tenant's total paid amount
- ✅ Payment history tracking

### 5.8 Dashboard & Analytics
- ✅ Overview statistics
  - Total tenants
  - Total landlords
  - Total properties
  - Occupied vs vacant properties
  - Active contracts
  - Unpaid invoices
  - Total monthly income
  - Total deposits
- ✅ Real-time data aggregation

### 5.9 Email Integration
- ✅ Resend email service integration
- ✅ Send emails via API
- ✅ Prepared for contract/invoice email delivery

---

## 6. Phase 2 Features (Deferred)

### 6.1 WhatsApp Integration
- WhatsApp Business API integration
- Send contracts via WhatsApp
- Send invoices via WhatsApp
- Delivery status tracking

### 6.2 OCR Passport Extraction
- OpenAI Vision integration (GPT-4o)
- Upload passport images
- Auto-extract passport information
- Manual review and correction

### 6.3 Hospitality Document Module
- Template-based document generation
- Auto-fill from tenant/property data
- PDF export
- Email and WhatsApp delivery

### 6.4 Reports
- Monthly income reports
- Outstanding payments report
- Deposit report
- Occupancy report
- Contract status report
- Landlord-wise income report
- Export to PDF/Excel

### 6.5 Notifications & Reminders
- Rent due date reminders
- Contract expiry alerts
- Passport expiry alerts
- Deposit reminders
- Automated email notifications

### 6.6 Audit Logs
- Track all user actions
- Record creation/modification history
- Document generation logs
- Payment transaction logs
- Timestamp and user tracking

### 6.7 Advanced Dashboard
- Charts and graphs
- Trend analysis
- Predictive analytics
- Revenue forecasting

---

## 7. API Endpoints

### 7.1 Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh access token

### 7.2 Tenants
- `POST /api/tenants` - Create tenant
- `GET /api/tenants` - List tenants
- `GET /api/tenants/{id}` - Get tenant details
- `PUT /api/tenants/{id}` - Update tenant
- `DELETE /api/tenants/{id}` - Delete tenant

### 7.3 Landlords
- `POST /api/landlords` - Create landlord
- `GET /api/landlords` - List landlords
- `GET /api/landlords/{id}` - Get landlord details
- `PUT /api/landlords/{id}` - Update landlord
- `DELETE /api/landlords/{id}` - Delete landlord

### 7.4 Properties
- `POST /api/properties` - Create property
- `GET /api/properties` - List properties
- `GET /api/properties/{id}` - Get property details
- `PUT /api/properties/{id}` - Update property
- `DELETE /api/properties/{id}` - Delete property

### 7.5 Contracts
- `POST /api/contracts` - Create contract
- `GET /api/contracts` - List contracts
- `GET /api/contracts/{id}` - Get contract details
- `PUT /api/contracts/{id}/status` - Update contract status
- `GET /api/contracts/{id}/pdf` - Download contract PDF

### 7.6 Invoices
- `POST /api/invoices` - Create invoice
- `GET /api/invoices` - List invoices
- `GET /api/invoices/{id}` - Get invoice details
- `GET /api/invoices/{id}/pdf` - Download invoice PDF

### 7.7 Payments
- `POST /api/payments` - Record payment
- `GET /api/payments/tenant/{tenant_id}` - Get tenant payments

### 7.8 Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

### 7.9 Email
- `POST /api/send-email` - Send email

---

## 8. UI/UX Structure

### 8.1 Pages
1. **Login** - `/login`
2. **Dashboard** - `/`
3. **Tenants** - `/tenants`
4. **Tenant Detail** - `/tenants/:id`
5. **Landlords** - `/landlords`
6. **Landlord Detail** - `/landlords/:id`
7. **Properties** - `/properties`
8. **Contracts** - `/contracts`
9. **Invoices** - `/invoices`

### 8.2 Components
- **Layout** - Main app shell with sidebar navigation
- **ProtectedRoute** - Route guard for authentication
- **Dialog** - Modal dialogs for forms
- **Table** - Data tables with sorting and filtering
- **Forms** - Input forms with validation
- **Cards** - Stat cards and info cards
- **Buttons** - Action buttons with icons

---

## 9. Security Considerations

### 9.1 Implemented
- JWT-based authentication
- Bcrypt password hashing (cost factor 10)
- HTTP-only cookies for token storage
- CAPTCHA on login
- MongoDB injection prevention (parameterized queries)
- CORS configuration
- Input validation (Pydantic models)
- Secure password requirements

### 9.2 Recommended for Production
- HTTPS enforcement
- Rate limiting
- Brute force protection
- Session timeout
- Two-factor authentication
- API key rotation
- Data encryption at rest
- Regular security audits

---

## 10. Environment Variables

### Backend (.env)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="property_management_db"
CORS_ORIGINS="*"
JWT_SECRET="<64-char-hex-string>"
ADMIN_EMAIL="admin@propertyops.com"
ADMIN_PASSWORD="Admin@123"
RESEND_API_KEY=""
SENDER_EMAIL="onboarding@resend.dev"
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://property-ops-16.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

---

## 11. Admin Credentials

**Email:** admin@propertyops.com  
**Password:** Admin@123  
**Role:** super_admin

---

## 12. Development Workflow

### 12.1 Setup
1. Install backend dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `yarn install`
3. Configure environment variables
4. Start MongoDB
5. Run backend: FastAPI with Uvicorn (via supervisor)
6. Run frontend: React dev server (via supervisor)

### 12.2 Key Files
- `/app/backend/server.py` - Main backend application
- `/app/frontend/src/App.js` - Main React application
- `/app/design_guidelines.json` - UI/UX design system
- `/app/memory/PRD.md` - This document
- `/app/memory/test_credentials.md` - Test credentials

---

## 13. Future Enhancements

### 13.1 Technical Improvements
- Implement caching (Redis)
- Add full-text search (Elasticsearch)
- Implement event-driven architecture
- Add WebSocket for real-time updates
- Migrate to microservices (if needed)
- Add comprehensive unit/integration tests

### 13.2 Feature Enhancements
- Multi-language support
- Mobile app (React Native)
- Tenant portal
- Online payment gateway integration
- Document e-signing
- Property maintenance tracking
- Expense management
- Accounting integration (QuickBooks, Xero)
- Calendar view for contracts/payments
- Bulk operations (import/export)

---

## 14. Success Metrics

### 14.1 MVP Success Criteria
- ✅ User authentication working
- ✅ All CRUD operations functional
- ✅ PDF generation working
- ✅ Dashboard showing accurate statistics
- ✅ Search and filter working
- ✅ Responsive design
- ✅ Professional UI/UX
- ✅ Email service configured

### 14.2 Performance Targets
- Page load time < 2 seconds
- API response time < 500ms
- Database query time < 100ms
- PDF generation time < 3 seconds

---

## 15. Known Limitations (MVP)

1. **Email Service:** Resend API key required for email functionality
2. **CAPTCHA:** Using Google reCAPTCHA test site key
3. **Scalability:** Single server deployment
4. **File Storage:** No document/image upload yet (Phase 2)
5. **Reporting:** Limited to dashboard stats (Phase 2)
6. **Notifications:** Manual email sending only (Phase 2)
7. **Multi-tenancy:** Single organization support

---

## 16. Deployment Checklist

- [ ] Configure production MongoDB
- [ ] Set production JWT secret
- [ ] Configure Resend API key
- [ ] Set up production CAPTCHA keys
- [ ] Enable HTTPS
- [ ] Configure production CORS
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Perform security audit
- [ ] Load testing
- [ ] User acceptance testing

---

## 17. Support & Documentation

### 17.1 User Guides
- Admin user guide (to be created)
- Operator manual (to be created)
- API documentation (to be created)

### 17.2 Technical Documentation
- Database schema (this document)
- API reference (this document)
- Deployment guide (to be created)
- Troubleshooting guide (to be created)

---

**Document Prepared By:** Emergent AI Agent  
**Approval Status:** MVP Complete  
**Next Review Date:** After Phase 2 completion
