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
- Deposit is a **constant guarantee** amount
- Deposit is NEVER reduced or subtracted
- Deposit is NOT used to pay rent
- Deposit stays the same value forever

### Payment Logic
- Tenants pay rent monthly, separately from deposit
- Each payment is linked to a tenant
- Payment status per tenant per month: Paid / Not Paid
- Payment shows: amount, method (Cash/Bank Transfer), date
- No remaining balance calculations
- No negative numbers anywhere in the system

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
- Full CRUD: Tenants, Landlords, Properties, Rooms, Contracts, Invoices, Payments
- Document upload (passport, ID, other)
- Room assignment and occupancy tracking
- Contract and Invoice PDF generation
- Notifications (overdue, upcoming, expiring)
- Reports with PDF export

### Phase 3: Advanced Features (DONE - 2026-04-21)
- OCR Passport/ID scanning (OpenAI Vision gpt-4o-mini)
- Hospitality PDF Template (Ospitalità)
- Excel/CSV Import & Export
- Backend refactored to modular architecture

### Phase 4: Simplified Payment Logic (DONE - 2026-04-21)
- Removed total_paid, total_due, remaining_balance from tenants
- Deposit is constant guarantee only
- Current month payment status per tenant (Paid/Not Paid)
- Payments page grouped by Property → Room → Tenant
- Dashboard shows monthly stats (collected, paid count, not-paid count)
- Green = Paid, Red = Not Paid throughout UI
- No negative numbers anywhere
- DB migration: removed legacy fields from all tenant records

---

## Backlog

### P1
- Real email integration (Resend/SendGrid) for OTP and notifications
- WhatsApp Business API for reminders

### P2
- Persian UI option
- Tenant self-service portal

---

## Architecture
```
/app/backend/
  server.py              # App setup (~90 lines)
  auth.py                # Auth module
  database.py            # MongoDB connection
  notifications.py       # Notification service (console)
  invoice_generator.py   # PDF invoice gen
  models/schemas.py      # Pydantic models
  routes/                # 14 route modules
  services/              # OCR, Hospitality PDF, Excel
  uploads/

/app/frontend/src/
  components/            # Layout, OcrScanner, ProtectedRoute
  pages/                 # All pages including DataExchange
```
