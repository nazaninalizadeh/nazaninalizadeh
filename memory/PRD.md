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
- DONE (Feb 27, 2026): Login auto-redirect fix — after successful login, navigates to / immediately; authenticated users hitting /login are bounced to / via <Navigate>

## Backlog
- P1: Real Resend/SendGrid integration for email reminders (currently mocked, logs to console)
- P1: WhatsApp Business API for ZIP package sharing (currently UI-only)
- P2: Add data-testid for Properties expand chevron + room action buttons (testing automation)
- P2: File mimetype/size allowlist on /properties|/rooms image upload endpoints
- P2: Scope single-admin session invalidation by admin_id (don't kill same admin's other tabs)
- P2: Replace window.alert kick UX with toast/modal
- P2: Aggregate /notifications/count to fix N+1 query
- P2: Unique compound index on monthly_status(tenant_id, month, year)
- P2: Persian UI translation
