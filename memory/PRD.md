# PropertyOps - Consulenze immobiliari - PRD

## Admins
- alborz.sbd@gmail.com (super_admin) / 1234@Admin
- nazaninalizade890@gmail.com (admin) / 1234@Admin

## Navigation (13 items)
Dashboard | Immobili | Stanze | Inquilini | Pagamenti | Ospitalita | Registrazione | Contratti | Fatture | Proprietari | Notifiche | Report | Gestione Dati

## Key Features
- Monthly Payment Status: manual override (Paid/Not Paid/Late) + auto-late from contract due dates
- Payment Calendar: 12-month visual tracker per tenant, clickable to change status
- Dashboard: late tenant details with links to profiles
- Notifications: auto-generated late payment alerts
- OCR: passport/ID scanning for tenants + owners
- Hospitality: COMUNICAZIONE DI OSPITALITA PDF
- Ricevuta: brand receipt PDF
- Registration: document upload + ZIP bundle
- Excel/CSV: import/export
- Searchable dropdowns: property + tenant search
- Auto property codes (IMM-XXXX)

## Data Model
- monthly_status: { tenant_id, month, year, status, amount, payment_method, manual_override, notes, updated_by, updated_at }
- Priority: manual override > payment records > auto-calculate from due_day

## Backlog
- P1: Real email (Resend/SendGrid), WhatsApp API
- P2: Persian UI
