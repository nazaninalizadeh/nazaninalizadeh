# PropertyOps - Consulenze immobiliari - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python) — Modular Architecture
- Database: MongoDB
- Auth: JWT + CAPTCHA + Single-device sessions
- OCR: OpenAI Vision (gpt-4o) via emergentintegrations
- PDF: ReportLab
- Excel: openpyxl

## Admins
- Admin 1: alborz.sbd@gmail.com (super_admin)
- Admin 2: nazaninalizade890@gmail.com (admin)
- Password: 1234@Admin

---

## Implemented Features

### Phase 1: Security (DONE - 2026-04-09)
- 2 whitelisted admins, no signup, no demo
- Direct login + CAPTCHA
- Single-device session enforcement
- Rate limiting, brute force protection, session timeout
- Activity logging, password change
- OTP infrastructure ready (disabled per user request)

### Phase 2: Complete System (DONE - 2026-04-21)

**Tenant Management:**
- Full CRUD with Codice Fiscale, passport, identity docs
- Property/room assignment from tenant form
- Partial payment tracking + remaining balance auto-calc
- Document upload (passport, ID, other)
- Payment history on detail page
- Link to contracts, invoices

**Landlord Management:**
- Full CRUD with Codice Fiscale, identity docs
- Occupancy overview (total rooms, occupied, vacant)
- Property list per landlord
- Financial summary

**Property Management:**
- Full CRUD linked to landlords
- Room count and occupancy status
- Tenant list per property

**Room Management:**
- Create rooms per property (single/double type)
- Room status tracking (available/occupied)
- Assign/unassign tenants to rooms
- Room image upload
- Bill responsibility tracking

**Payment System:**
- Register payments (partial or full)
- Link payment to invoice (auto-updates paid_amount)
- Payment methods: contanti, bonifico, carta, assegno
- Remaining balance auto-calculation on tenant
- Payment history with search

**Reports:**
- Weekly/monthly/yearly report generation
- PDF export with summary tables
- Tenant balances, occupancy rates, payment stats

**Notifications:**
- Overdue payment alerts (severity: high)
- Upcoming payments (next 7 days)
- Expiring contracts (next 30 days)
- Expiring passports (next 90 days)
- Birthday notifications
- Severity-based sorting

**Dashboard:**
- Stats cards: tenants, landlords, properties, rooms, contracts, invoices
- Financial summary: monthly income, collected, outstanding, deposits
- Room occupancy bar with percentage
- Recent payments list

**Contract Management:**
- Full CRUD with PDF generation
- Auto contract numbering
- Status management (active/expired/cancelled)

**Invoice Management:**
- Full CRUD with PDF generation
- Partial payment status (paid/partial/unpaid)
- Auto-update on payment registration

**Document Management:**
- File upload for tenants and landlords
- Types: passport, id_card, other
- Download and delete functionality

### Phase 3: Advanced Features (DONE - 2026-04-21)

**OCR Passport/ID Scanning (P1):**
- OpenAI Vision (gpt-4o) integration via emergentintegrations
- Automatic extraction: full name, passport number, nationality, DOB, gender, place of birth, issue/expiry dates, codice fiscale
- Auto-fill tenant form with extracted data
- Admin review before saving
- OCR status tracking (pending/processing/completed/failed)
- Confidence indicator (high/medium/low)
- Supports JPEG, PNG, WebP up to 10MB

**Hospitality PDF Template - Ospitalità (P1):**
- Professional dichiarazione di ospitalità document
- Includes tenant, landlord, property, and room data
- Contract dates auto-populated from active contracts
- Official Italian legal formatting with signature areas
- Downloadable from tenant detail page

**Excel/CSV Import & Export (P2):**
- Export tenants to Excel with all fields
- Export payments to Excel with tenant names
- Export occupancy data (property → rooms → tenants)
- Import tenants from Excel/CSV with validation
- Import payments from Excel/CSV with tenant lookup
- Downloadable sample templates
- Row-by-row error reporting
- Duplicate detection (passport number)

**Backend Refactoring (P2):**
- server.py: 1072 lines → ~90 lines (thin orchestrator)
- 11 route modules in routes/
- 3 service modules in services/
- Pydantic models in models/schemas.py
- Clean separation of concerns

---

## Backlog

### P1
- Real email integration (Resend/SendGrid) for OTP and notifications
- WhatsApp Business API for reminders

### P2
- Persian UI option
- Tenant self-service portal
- Advanced audit log viewer

---

## Architecture
```
/app/backend/
  server.py              # App setup + router includes (~90 lines)
  auth.py                # Auth module (JWT, sessions, OTP)
  database.py            # MongoDB connection
  notifications.py       # Notification service (console)
  invoice_generator.py   # PDF invoice gen
  models/
    schemas.py           # All Pydantic models
  routes/
    tenants.py           # Tenant CRUD
    landlords.py         # Landlord CRUD
    properties.py        # Property CRUD
    rooms.py             # Room CRUD + occupancy overview
    contracts.py         # Contract CRUD + PDF
    invoices.py          # Invoice CRUD + PDF
    payments.py          # Payment CRUD
    documents.py         # Document upload/download
    dashboard.py         # Dashboard stats
    reports.py           # Report generation + PDF
    notifications_routes.py  # Notifications API
    ocr.py               # OCR scanning endpoints
    hospitality.py       # Hospitality PDF endpoints
    data_exchange.py     # Import/Export endpoints
  services/
    ocr_service.py       # OpenAI Vision OCR logic
    hospitality_pdf.py   # Ospitalità PDF generation
    excel_service.py     # Excel/CSV import/export logic
  uploads/

/app/frontend/src/
  context/AuthContext.js
  components/Layout.js, ProtectedRoute.js, OcrScanner.js
  pages/Dashboard.js, Tenants.js, TenantDetail.js,
        Landlords.js, LandlordDetail.js, Properties.js,
        Rooms.js, Payments.js, Contracts.js, Invoices.js,
        Notifications.js, Reports.js, DataExchange.js, Login.js
```
