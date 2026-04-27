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
- DONE (Feb 27, 2026): Inside Immobili tenant assign/unassign with searchable dropdown (real tenant data)
- DONE (Feb 27, 2026): data-testid coverage for property/room actions
- DONE (Feb 27, 2026): Image upload security — JPG/PNG/WEBP only, 5MB max, mimetype + ext check, client + server
- DONE (Feb 27, 2026): Single-device-per-account session — invalidation scoped by admin_id
- DONE (Feb 27, 2026): window.alert → sonner toast for session-kicked UX
- DONE (Feb 27, 2026): /notifications/count optimized — 3 bulk queries (sub-200ms)
- DONE (Feb 27, 2026): Email reminder structure (1 wk before / 1 day after / 1 wk after)
- DONE (Feb 27, 2026): Dashboard count consistency — `tenants_late = len(late_details)` (single source of truth)
- DONE (Feb 27, 2026): Hospitality PDF rebuilt to match official Italian template exactly (no extra branding)
- DONE (Feb 27, 2026): Notification badge — POST /api/notifications/mark-seen + last_viewed_at vs became_late_at; sidebar listens for 'notifications:seen' event
- DONE (Feb 27, 2026): Tenant document download bug — `/uploads/` was hitting K8s ingress and Navigate('/'); now serves at `/api/uploads/` + DB migration
- DONE (Feb 27, 2026): Real Resend email integration with mock fallback when RESEND_API_KEY is empty (services/email_service.py)

## Backlog
- P1: Provide RESEND_API_KEY in production .env to switch reminders from mock to real
- P1: WhatsApp Business API for ZIP sharing (currently UI-toast)
- P2: Replace test RECAPTCHA_SECRET with production key (or remove)
- P2: Persian UI translation
- P2: Unique compound index on monthly_status(tenant_id, month, year)
- P2: Edge case in _became_late_at for due_day > 28 (clamps to 28)
