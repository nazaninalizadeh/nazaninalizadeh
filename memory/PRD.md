# PropertyOps - Consulenze immobiliari - PRD

## Admins
- alborz.sbd@gmail.com (super_admin) / 1234@Admin
- nazaninalizade890@gmail.com (admin) / 1234@Admin

## Security
- Single-admin session: only ONE admin active at a time
- New login invalidates all other sessions immediately
- Frontend polls /session-check every 30s → auto-logout if session invalidated
- Shows "Another admin logged in" alert

## Navigation (12 items)
Proprietari | Immobili | Inquilini | Dashboard | Pagamenti | Ospitalità | Registrazione | Contratti | Fatture | Notifiche (with badge) | Report | Gestione Dati

## Payment System
- 3 statuses: Pagato (green) / Non Pagato (amber) / In Ritardo (red)
- In Ritardo: automatically triggered 1 day after contract due_day
- due_day comes from contract first, fallback to tenant.payment_due_day
- Manual override: admin can change any month status
- Payment method: selectable buttons (Contanti / Bonifico) — NOT typed
- Cancel button: closes dialog without changing anything

## Key Features
- Monthly Payment Calendar: 12-month clickable tracker per tenant
- Notification badge: red count on Notifiche menu item
- Dashboard: late tenant details section + clickable stats
- OCR: passport/ID scanning + file permanently saved
- Hospitality: COMUNICAZIONE DI OSPITALITA PDF
- Registration: document upload + ZIP bundle
- Auto property codes (IMM-XXXX)
- Searchable dropdowns: property + tenant search

## Recently Completed (Feb 2026)
- DONE: Merge Stanze into Immobili detail (rooms visible when clicking property)
- DONE: Image upload for properties/rooms
- DONE: Owner ID front/back upload with OCR
- DONE: Registration ZIP package (visual share buttons)
- DONE: Face detection for profile photo
- DONE: Login page redesign (dark navy + cream card + red accent)
- DONE (Feb 27, 2026): Login auto-redirect — navigate('/') + <Navigate /> guard
- DONE (Feb 27, 2026): Menu order — Dashboard, Proprietari, Immobili, Inquilini, then rest
- DONE (Feb 27, 2026): Inside Immobili tenant assign/unassign with searchable dropdown
- DONE (Feb 27, 2026): data-testid coverage for property/room actions
- DONE (Feb 27, 2026): Image upload security — JPG/PNG/WEBP only, 5MB max, mimetype + ext check
- DONE (Feb 27, 2026): Single-device-per-account session — invalidation scoped by admin_id
- DONE (Feb 27, 2026): window.alert → sonner toast for session-kicked UX
- DONE (Feb 27, 2026): /notifications/count optimized — 3 bulk queries
- DONE (Feb 27, 2026): Email reminder structure (1 wk before / 1 day after / 1 wk after)
- DONE (Feb 27, 2026): Dashboard count consistency — `tenants_late = len(late_details)`
- DONE (Feb 27, 2026): Hospitality PDF rebuilt drawn-from-scratch matching JALLAB template
- DONE (Feb 27, 2026): Notification badge mark-seen + last_viewed_at vs became_late_at
- DONE (Feb 27, 2026): Tenant document download — `/uploads/` → `/api/uploads/`
- DONE (Feb 27, 2026): Real Resend email integration with mock fallback
- DONE (Feb 28, 2026): **Group 1 + Group 2 + Group 3 batch updates (25+ items)**:
   - DD/MM/YYYY date format util (`/lib/format.js`) wired into Contracts/Payments/Invoices tables
   - WhatsApp → Phone everywhere (Tenants/Owners/Properties forms; legacy whatsapp field optional)
   - DELETE buttons + backend routes for Contratti and Pagamenti (Payment delete reverses invoice paid_amount)
   - "Piano" field removed from rooms; double rooms display "(€350 a persona)" automatically
   - ZIP package shows 5-item file list bullet
   - OCR PDF support — pdftoppm renders first page → vision model
   - OCR enhanced — country code (IRN/ITA/MAR…) → full Italian name
   - Italian dictionaries (`it_dictionaries.js`): 116 nationalities + 116 countries + 107 provinces
   - Reusable `Combobox` component for searchable autocomplete
   - Province dropdown on Properties (default PD-Padova)
   - Property type Select: Appartamento / Studio
   - Single/Double room counts on property card + API
   - Surname → Name order in Tenants & Owners (full_name = "Surname Name")
   - Owner signature upload with PIL transparent-PNG conversion
   - Payment dialog auto-fills rent (halved if room.room_type='double')
   - Hospitality auto-fills check_in_date from active contract; default duration 1 year; signature image overlay
   - "Luogo e data: Padova, DD/MM/YYYY" (city title-cased + Italian date)
   - Invoice dynamic panel: Affitto + Deposito + Spese agenzia + Registrazione (default 98) + Sconto + auto-computed TOTALE
   - Invoice auto-fill on tenant select (property + contract + rent + deposit)

## DONE (Apr 30, 2026): Room reassignment orphan-fix + Property Photo Gallery + Invoice PDFs
- BUG FIX: `POST /api/rooms/{id}/assign` now clears orphan `tenant.room_id` when assigning to an already-occupied room (rooms.py:113-121)
- FEATURE — Property Photo Gallery Lightbox:
   - Click any property thumbnail in expanded Immobili card → full-screen lightbox
   - Navigation: prev/next arrows, thumbnail strip, counter (1/N)
   - Delete button removes photo via DELETE /api/properties/{id}/images?url=...
   - data-testids: property-photo-thumb-{pid}-{i}, property-gallery-lightbox, gallery-close/prev/next/delete/main-image, gallery-thumb-{i}
- FEATURE — Invoice PDFs (2 types, pixel-drawn via ReportLab):
   - `/app/backend/services/invoice_pdf.py` with generate_fattura_pdf() + generate_preavviso_pdf()
   - Fattura: replica of COEB example (DESCRIZIONE/IMPORTO + RIEPILOGO IVA box + MODALITA'/SCADENZE footer)
   - Preavviso: replica of ELEISON example (Spett.le + CAUSALE line + TOTALE FATTURA + BONIFICO BANCARIO PRESSO)
   - Preavviso accepts commercial recipients without a tenant (empty tenant_id/property_id allowed)
   - Frontend: toggle tab [doc-type-fattura | doc-type-preavviso] switches input forms
   - Live TOTAL = imponibile*(1+vat%) + rimborso (preavviso) or rent+dep+ag+reg-disc (fattura)
- Tested via /app/test_reports/iteration_17.json (100% backend 7/7, 100% frontend 2/2)

## Backlog
- P1: WhatsApp Business API for ZIP sharing (currently UI-toast)
- P2: Replace test RECAPTCHA_SECRET with production key (or remove)
- P2: Persian UI translation
- P2: Fmt remaining table date columns app-wide (Tenants list passport_expiry, Dashboard activity, Reports)
- P2: Make signature transparency threshold tunable (currently hard-coded RGB > 235)
- P2: Aggregate room counts in single $facet pipeline (current: N+1 per property)
