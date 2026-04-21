# PropertyOps - Consulenze immobiliari - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python) — Modular Architecture
- Database: MongoDB
- Auth: JWT + CAPTCHA + Single-device sessions
- OCR: OpenAI Vision (gpt-4o-mini) via emergentintegrations
- PDF: ReportLab
- Excel: openpyxl

## Admins
- Admin 1: alborz.sbd@gmail.com (super_admin)
- Admin 2: nazaninalizade890@gmail.com (admin)
- Password: 1234@Admin

---

## Business Rules

### Deposit (CRITICAL)
- Deposit is a **constant guarantee** amount - NEVER reduced
- NOT used to pay rent

### Payment Logic
- Tenants pay rent monthly, separately from deposit
- Payment status per tenant per month: Paid / Not Paid
- No remaining balance, no negative numbers

### Data Connections
- Tenant ↔ Property ↔ Room are linked
- Payment ↔ Tenant is linked
- All data visible across pages (Inquilini, Immobili, Pagamenti, Stanze)

---

## Implemented Features

### Phase 1: Security (DONE)
- 2 whitelisted admins, no signup
- JWT + CAPTCHA + single-device sessions
- Rate limiting, brute force protection

### Phase 2: Complete System (DONE)
- Full CRUD: Tenants, Landlords, Properties, Rooms, Contracts, Invoices, Payments
- Document upload, Room assignment, Contract/Invoice PDFs
- Notifications, Reports with PDF export

### Phase 3: Advanced Features (DONE)
- OCR Passport/ID scanning (OpenAI Vision gpt-4o-mini)
- Hospitality PDF Template (Ospitalita)
- Excel/CSV Import & Export
- Backend refactored to modular architecture

### Phase 4: Simplified Payment Logic (DONE)
- Deposit constant, current month Paid/Not Paid per tenant
- Payments grouped by Property → Room → Tenant
- Dashboard with monthly stats

### Phase 5: Data Connections Fix (DONE - 2026-04-21)
- Payment form dropdown shows ALL tenants with name + property + room
- Tenants page shows "Non assegnato" clearly for unassigned tenants
- Properties page: expandable cards showing rooms with tenant names
- All modules interconnected: Inquilini ↔ Proprieta ↔ Stanze ↔ Pagamenti

---

## Backlog
### P1
- Real email integration (Resend/SendGrid)
- WhatsApp Business API

### P2
- Persian UI option
- Tenant self-service portal

---

## Architecture
```
/app/backend/
  server.py, auth.py, database.py, notifications.py, invoice_generator.py
  models/schemas.py
  routes/ (14 modules)
  services/ (OCR, Hospitality PDF, Excel)
  uploads/
/app/frontend/src/
  components/ (Layout, OcrScanner, ProtectedRoute)
  pages/ (Dashboard, Tenants, TenantDetail, Landlords, Properties, Rooms, 
          Payments, Contracts, Invoices, Notifications, Reports, DataExchange, Login)
```
