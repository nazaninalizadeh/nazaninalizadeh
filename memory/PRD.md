# PropertyOps - Consulenze immobiliari - PRD

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python) — Modular Architecture
- Database: MongoDB
- Auth: JWT + CAPTCHA + Single-device sessions
- OCR: OpenAI Vision (gpt-4o-mini)
- PDF: ReportLab
- Excel: openpyxl

## Admins
- Admin 1: alborz.sbd@gmail.com (super_admin)
- Admin 2: nazaninalizade890@gmail.com (admin)
- Password: 1234@Admin

---

## Architecture: Connected Data Model

### Entity Relationships
- Property → has many Rooms
- Room → belongs to Property, has one Tenant (if occupied)
- Tenant → assigned to Property + Room
- Payment → belongs to Tenant
- Landlord → owns Properties
- Hospitality PDF → generated from Tenant + Property + Room + Landlord data

### Dynamic Connections
All pages read from the same data. Changes propagate automatically:
- Tenant assignment → visible in Inquilini, Immobili, Stanze, Pagamenti, Ospitalita
- Payment added → visible in Pagamenti, Inquilini (Stato Mese), Dashboard
- Room created → visible in Stanze, Immobili (expanded detail)

---

## Navigation (Sidebar Order)
1. Dashboard
2. Immobili (Properties - unified, expandable with rooms/tenants)
3. Stanze (Room management)
4. Inquilini (Tenants with payment status)
5. Pagamenti (Payments grouped by property)
6. Ospitalita (Hospitality PDF generation)
7. Contratti
8. Fatture
9. Proprietari (Landlords)
10. Notifiche
11. Report
12. Gestione Dati (Import/Export)

---

## Implemented Features (All DONE)

### Security: Auth, sessions, rate limiting, brute force
### CRUD: Tenants, Landlords, Properties, Rooms, Contracts, Invoices, Payments
### OCR: Passport/ID scanning with OpenAI Vision
### Hospitality: Ospitalita PDF with dedicated page
### Excel/CSV: Import & Export for tenants, payments, occupancy
### Simplified Payments: Deposit constant, monthly Paid/Not Paid
### Connected Architecture: All modules share data model

---

## Backlog
### P1
- Real email integration (Resend/SendGrid)
- WhatsApp Business API
### P2
- Persian UI option
- Tenant self-service portal
