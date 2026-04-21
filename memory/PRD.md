# PropertyOps - Consulenze immobiliari - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Auth: JWT + CAPTCHA + Single-device sessions

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

**Room Management (NEW):**
- Create rooms per property (single/double type)
- Room status tracking (available/occupied)
- Assign/unassign tenants to rooms
- Room image upload
- Bill responsibility tracking

**Payment System (NEW):**
- Register payments (partial or full)
- Link payment to invoice (auto-updates paid_amount)
- Payment methods: contanti, bonifico, carta, assegno
- Remaining balance auto-calculation on tenant
- Payment history with search

**Reports (ENHANCED):**
- Weekly/monthly/yearly report generation
- PDF export with summary tables
- Tenant balances, occupancy rates, payment stats

**Notifications (ENHANCED):**
- Overdue payment alerts (severity: high)
- Upcoming payments (next 7 days)
- Expiring contracts (next 30 days)
- Expiring passports (next 90 days)
- Birthday notifications
- Severity-based sorting

**Dashboard (ENHANCED):**
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

---

## Backlog

### P1
- Real email integration (Resend/SendGrid) for OTP and notifications
- WhatsApp Business API
- Passport OCR with OpenAI Vision
- Hospitality document PDF

### P2
- Excel/CSV import/export
- Tenant portal
- Advanced audit log viewer
- Persian UI option

---

## Architecture
```
/app/backend/
  server.py          # Main app + all CRUD routes
  auth.py            # Auth module
  database.py        # MongoDB connection
  notifications.py   # Notification service (console)
  invoice_generator.py # PDF invoice gen
  uploads/           # Document/room image storage

/app/frontend/src/
  context/AuthContext.js
  components/Layout.js, ProtectedRoute.js
  pages/Dashboard.js, Tenants.js, TenantDetail.js,
        Landlords.js, LandlordDetail.js, Properties.js,
        Rooms.js, Payments.js, Contracts.js, Invoices.js,
        Notifications.js, Reports.js, Login.js
```
