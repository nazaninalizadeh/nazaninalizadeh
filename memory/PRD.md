# PropertyOps - Consulenze immobiliari - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python) — Modular Architecture
- Database: MongoDB
- Auth: JWT + CAPTCHA + Single-device sessions
- OCR: OpenAI Vision (gpt-4o-mini) via emergentintegrations
- PDF: ReportLab (Hospitality + Ricevuta + Contracts + Reports)
- Excel: openpyxl

## Admins
- alborz.sbd@gmail.com (super_admin) / 1234@Admin
- nazaninalizade890@gmail.com (admin) / 1234@Admin

---

## Navigation (12 items)
Dashboard | Immobili | Stanze | Inquilini | Pagamenti | Ospitalita | Contratti | Fatture | Proprietari | Notifiche | Report | Gestione Dati

---

## Implemented Features

### Security: Auth, sessions, CAPTCHA, brute force, rate limiting
### CRUD: Tenants, Landlords, Properties, Rooms, Contracts, Invoices, Payments
### OCR: Passport/ID scanning (OpenAI Vision gpt-4o-mini)
### Hospitality (Ospitalita):
- COMUNICAZIONE DI OSPITALITA' form matching Italian government template (Art. 7 D.Lvo 286/98)
- Create form with OCR, host/guest details, property details, dates
- CRUD for hospitality records
- PDF generation from tenant+property+landlord data
### Ricevuta (Receipt/Invoice):
- Brand PDF matching Consulenze immobiliari design (logo, tagline, VIA VIGONOVESE 114)
- Receipt number, date, time, amount (numerical + Italian words)
- "Ricevuto da" tenant name, "Per" description lines
- Generate from payment records or custom data
- Download button on each payment in Pagamenti history
### Excel/CSV: Import & Export
### Simplified Payments: Deposit constant, monthly Paid/Not Paid
### Connected Architecture: All modules share data model

---

## Key Data Points
- Properties: 2 (via cristoforis 15, via piovese 142)
- Rooms: 0 (need to be created via Stanze page)
- Tenants: 6
- Payments: 3

## Backlog
### P1
- Real email (Resend/SendGrid) for OTP and notifications
- WhatsApp Business API
### P2
- Persian UI option
