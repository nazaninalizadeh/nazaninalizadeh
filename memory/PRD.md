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
- DONE: Hospitality form exact match to provided form
- DONE: Owner ID front/back upload with OCR
- DONE: Registration ZIP package (visual share buttons)
- DONE: Face detection for profile photo
- DONE: Login page redesign (dark navy + cream card + red accent)
- DONE (Feb 27, 2026): Login auto-redirect — navigate('/') + <Navigate /> guard
- DONE (Feb 27, 2026): Menu order — Dashboard, Proprietari, Immobili, Inquilini, then rest
- DONE (Feb 27, 2026): Inside Immobili tenant assign/unassign with searchable dropdown (real tenant data)
- DONE (Feb 27, 2026): data-testid for expand-property, assign-room, unassign-room, delete-room, upload-property-image, upload-room-image, edit/delete-property, assign-tenant-search/list/option/confirm, zip-wa/email/download
- DONE (Feb 27, 2026): Image upload security — JPG/PNG/WEBP only, 5MB max, mimetype + ext check; clear 400/413 errors; both client + server side
- DONE (Feb 27, 2026): Single-device-per-account session — invalidation scoped by admin_id (admin1 and admin2 sessions independent; same admin's tabs share cookie)
- DONE (Feb 27, 2026): Replaced window.alert with sonner toast for session-kicked UX (non-blocking)
- DONE (Feb 27, 2026): /notifications/count optimized — 3 bulk queries instead of N+1 (sub-200ms)
- DONE (Feb 27, 2026): Email reminders — structured for Resend/SendGrid; logs 1-week-before / 1-day-after / 1-week-after
- DONE (Feb 27, 2026): WhatsApp + Email mock share buttons in Registration ZIP

## Backlog
- P1: Real Resend/SendGrid integration (currently console-logged) — needs API key
- P1: WhatsApp Business API (currently UI-toast) — needs API key
- P2: Replace test RECAPTCHA_SECRET with real production key (or remove)
- P2: Persian UI translation
- P2: Unique compound index on monthly_status(tenant_id, month, year)
