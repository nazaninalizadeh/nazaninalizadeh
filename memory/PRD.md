# PropertyOps - Consulenze immobiliari
## Product Requirements Document

### Original Problem Statement
Complete web-based property rental and tenant management system managing tenants, landlords, properties, contracts, invoices, hospitality documents, monthly payments, passport data extraction, and document delivery through email and WhatsApp.

### Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Auth: JWT + Email OTP 2FA + CAPTCHA + Single-device sessions

### Admin Users
- Admin 1: alborz.sbd@gmail.com (super_admin) - Alborz
- Admin 2: nazaninalizade890@gmail.com (admin) - Nazanin
- NO other users, NO signup, NO demo access

---

## What's Been Implemented

### Phase 1: Security & Authentication (COMPLETE - 2026-04-09)
- 2 whitelisted admins only (no registration)
- 2-step login: Email + Password + CAPTCHA → Email OTP verification
- OTP: 6-digit, SHA-256 hashed, 5-min expiry, max 3 attempts
- Single-device session enforcement (new login invalidates previous)
- Session timeout: 8 hours inactivity
- Rate limiting: 10 auth requests per 60 seconds per IP
- Brute force protection: 5 failed attempts → 15-min lockout
- Activity logging (who, when, from where, what action)
- Password change endpoint (min 10 chars)
- JWT access tokens (30 min) + refresh tokens (7 days)
- httpOnly cookies for token storage
- CAPTCHA (reCAPTCHA v2) on login
- Login notification logged to console (ready for email plug-in)
- Modular notification service (ready for Resend/SendGrid/WhatsApp)
- Demo credentials REMOVED from login page
- PostHog error suppression

### MVP CRUD (COMPLETE - earlier sessions)
- Tenants: Full CRUD with search, passport data
- Landlords: Full CRUD with search, bank details
- Properties: Full CRUD with landlord association, occupancy tracking
- Contracts: Full CRUD with tenant/property linking, PDF download, status management
- Invoices: Full CRUD with payment tracking, PDF generation
- Dashboard: Stats overview (counts, revenue, occupancy)
- Notifications: Contract/passport expiry reminders
- Reports: Financial/operational report generation

### UI/Styling (PARTIAL)
- Italian translation throughout
- Luxury CSS classes created (index.css, App.css)
- Login page: luxury styling with 2FA flow
- Some pages updated with luxury styling, some still have old style

---

## Prioritized Backlog

### P0 - In Progress / Next
- Complete luxury CSS styling on ALL pages (Layout, Dashboard, all CRUD pages, detail pages)
- Hospitality PDF document generator (ospitalita template)
- Property room management (rooms, single/double, occupancy, tenant-room mapping)

### P1 - High Priority
- Tenant data improvements: Codice Fiscale, identity docs upload, house/room assignment, partial payments
- Landlord improvements: Codice Fiscale, identity docs, property occupancy summary
- Property improvements: Room system, room photos, tenant-room link, bill responsibility
- Printable reports: weekly/monthly/yearly PDF exports
- Passport OCR with OpenAI Vision

### P2 - Medium Priority
- Real email integration (Resend/SendGrid) for OTP and notifications
- WhatsApp Business API integration
- Payment reminders (upcoming, late, overdue)
- Automatic birthday greetings
- Session timeout UX improvement (auto-redirect)

### P3 - Future
- Tenant portal
- Excel/CSV bulk import/export
- Persian UI translation (if requested)
- Audit log viewer in admin panel

---

## Architecture

```
/app/
├── backend/
│   ├── server.py              # Main app + CRUD routes
│   ├── auth.py                # Auth module (2FA, sessions, rate limiting)
│   ├── database.py            # Shared MongoDB connection
│   ├── notifications.py       # Pluggable notification service
│   ├── invoice_generator.py   # PDF invoice generation
│   ├── phase2_routes.py       # Additional routes
│   └── .env                   # Environment variables
├── frontend/
│   ├── src/
│   │   ├── context/AuthContext.js  # Auth state + 2-step flow
│   │   ├── components/Layout.js    # Sidebar + nav
│   │   ├── components/ProtectedRoute.js
│   │   └── pages/                  # All page components
│   └── public/index.html
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

### Key API Endpoints
- Auth: POST /api/auth/login-step1, POST /api/auth/verify-otp, GET /api/auth/me, POST /api/auth/logout, POST /api/auth/change-password, GET /api/auth/activity-logs
- Tenants: GET/POST /api/tenants, GET/PUT/DELETE /api/tenants/{id}
- Landlords: GET/POST /api/landlords, GET/PUT/DELETE /api/landlords/{id}
- Properties: GET/POST /api/properties, GET/PUT/DELETE /api/properties/{id}
- Contracts: GET/POST /api/contracts, GET/PUT/DELETE /api/contracts/{id}
- Invoices: GET/POST /api/invoices, GET/PUT/DELETE /api/invoices/{id}
- Dashboard: GET /api/dashboard/stats
- Reports: POST /api/reports/generate

### DB Collections
- users: email, password_hash, name, role, created_at
- sessions: session_id, admin_id, admin_email, ip_address, user_agent, is_active, created_at, last_active
- otp_codes: login_session_id, admin_email, otp_hash, attempts, created_at, expires_at, used, ip
- login_attempts: identifier, attempts, first_attempt, locked_until
- activity_logs: id, admin_email, action, ip_address, user_agent, details, timestamp
- tenants, landlords, properties, contracts, invoices
