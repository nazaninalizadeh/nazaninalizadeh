# PropertyOps - Consulenze immobiliari - PRD

## Admins
- alborz.sbd@gmail.com (super_admin) / 1234@Admin
- nazaninalizade890@gmail.com (admin) / 1234@Admin

## Navigation (13 items)
Dashboard | Immobili | Stanze | Inquilini | Pagamenti | Ospitalita | Registrazione | Contratti | Fatture | Proprietari | Notifiche | Report | Gestione Dati

## Business Rules
- Deposit: constant guarantee, never reduced
- Payment statuses: Paid / Not Paid / In Ritardo (Late)
- Start of month = Not Paid; after due day (default 5th) = Late; manual payment = Paid
- Payment method shown next to Paid status (Contanti/Bonifico)
- Property codes auto-generated (IMM-XXXX format)
- OCR saves original document + extracted data
- ZIP bundle: Hospitality + Registration + Contract + Owner docs

## Implemented (All DONE)
- Security: JWT + CAPTCHA + single-device sessions
- CRUD: Tenants, Landlords, Properties, Rooms, Contracts, Invoices, Payments
- OCR: Passport/ID scanning + original file saved + doc type detection
- Hospitality: COMUNICAZIONE DI OSPITALITA form + PDF + create form with OCR
- Ricevuta: Brand receipt PDF (Consulenze immobiliari design)
- Registration: Dedicated page with upload + ZIP bundle
- Excel/CSV: Import & Export
- 3 Payment Statuses with filter tabs
- Dashboard links to filtered tenant lists
- Room edit capability
- Contract + Owner document upload
- All modules dynamically connected

## Backlog
- P1: Real email (Resend/SendGrid), WhatsApp API
- P2: Persian UI option
