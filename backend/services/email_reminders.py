"""Email Reminder Service - uses email_service.send_email which routes to Resend
(when RESEND_API_KEY is configured) or falls back to a console-log mock. The 3
reminder windows are: 1 week BEFORE due day, 1 day AFTER, 1 week AFTER."""

import logging
from datetime import datetime, timezone
from database import db
from services.email_service import send_email

logger = logging.getLogger("email_reminders")

MONTH_NAMES = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


async def check_and_send_reminders():
    """Check all tenants for reminder triggers and send/log emails."""
    now = datetime.now(timezone.utc)
    today = int(now.strftime("%d"))
    current_month = now.month
    current_year = now.year
    month_start = now.strftime("%Y-%m-01")
    month_end = f"{now.year + 1}-01-01" if now.month == 12 else f"{now.year}-{now.month + 1:02d}-01"

    tenants = await db.tenants.find({"room_id": {"$ne": ""}}, {"_id": 0}).to_list(1000)

    for tenant in tenants:
        due_day = tenant.get("payment_due_day", 5)

        # Check if already paid this month
        override = await db.monthly_status.find_one(
            {"tenant_id": tenant["id"], "month": current_month, "year": current_year}, {"_id": 0}
        )
        if override and override.get("status") == "paid":
            continue
        payments = await db.payments.find(
            {"tenant_id": tenant["id"], "payment_date": {"$gte": month_start, "$lt": month_end}}, {"_id": 0}
        ).to_list(1)
        if payments:
            continue

        # Get property/room info
        prop_addr = ""
        room_num = ""
        if tenant.get("property_id"):
            prop = await db.properties.find_one({"id": tenant["property_id"]}, {"_id": 0})
            prop_addr = prop.get("address", "") if prop else ""
        if tenant.get("room_id"):
            room = await db.rooms.find_one({"id": tenant["room_id"]}, {"_id": 0})
            room_num = room.get("room_number", "") if room else ""

        # Determine which reminder to send
        days_until_due = due_day - today
        days_after_due = today - due_day

        if days_until_due == 7:
            await _send_reminder(
                tenant, prop_addr, room_num, due_day, "pre_reminder",
                subject=f"Promemoria affitto in scadenza — {prop_addr}",
                message=(
                    f"Gentile {tenant.get('full_name','')}, ricordiamo che il pagamento dell'affitto "
                    f"per {prop_addr} (Stanza {room_num}) scade il giorno {due_day} "
                    f"di {MONTH_NAMES[current_month]}. La preghiamo di provvedere entro la scadenza."
                ),
            )
        elif days_after_due == 1:
            await _send_reminder(
                tenant, prop_addr, room_num, due_day, "late_warning",
                subject=f"Affitto scaduto — {prop_addr}",
                message=(
                    f"Gentile {tenant.get('full_name','')}, il pagamento dell'affitto per {prop_addr} "
                    f"(Stanza {room_num}) risulta scaduto dal giorno {due_day}/{current_month:02d}/{current_year}. "
                    f"La preghiamo di provvedere al pagamento il prima possibile."
                ),
            )
        elif days_after_due == 7:
            await _send_reminder(
                tenant, prop_addr, room_num, due_day, "second_reminder",
                subject=f"SECONDO AVVISO — Affitto scaduto da una settimana — {prop_addr}",
                message=(
                    f"SECONDO AVVISO. Gentile {tenant.get('full_name','')}, il pagamento dell'affitto "
                    f"per {prop_addr} (Stanza {room_num}) risulta ancora non pagato. "
                    f"Scadenza originale: {due_day}/{current_month:02d}/{current_year}. "
                    f"La preghiamo di contattarci urgentemente."
                ),
            )


async def _send_reminder(tenant: dict, prop_addr: str, room_num: str, due_day: int,
                         reminder_type: str, *, subject: str, message: str):
    """Send a reminder email + persist a record."""
    to_email = tenant.get("email", "")

    html = f"""
<table width="100%" cellpadding="0" cellspacing="0" style="font-family: Arial, sans-serif; color: #2C1810; background:#FAF7F0; padding:24px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="background:#FFFBF5;border:1px solid rgba(184,134,11,0.2);border-radius:12px;overflow:hidden;">
      <tr><td style="background:#9F1239;color:#fff;padding:18px 24px;font-size:18px;font-weight:bold;">Consulenze immobiliari</td></tr>
      <tr><td style="padding:24px;">
        <p style="font-size:14px;line-height:1.6;margin:0 0 16px 0;">{message}</p>
        <table width="100%" cellpadding="6" cellspacing="0" style="background:rgba(159,18,57,0.04);border-radius:8px;font-size:13px;color:#5C4A3A;">
          <tr><td><b>Immobile:</b></td><td>{prop_addr}</td></tr>
          <tr><td><b>Stanza:</b></td><td>{room_num}</td></tr>
          <tr><td><b>Scadenza:</b></td><td>giorno {due_day} del mese</td></tr>
        </table>
        <p style="font-size:12px;color:#8B7355;margin-top:18px;">Per qualsiasi domanda risponda direttamente a questa email.</p>
      </td></tr>
      <tr><td style="background:#FAF7F0;padding:12px 24px;font-size:11px;color:#8B7355;">Consulenze immobiliari — Via Vigonovese 114</td></tr>
    </table>
  </td></tr>
</table>"""

    result = await send_email(to_email, subject, html)

    record = {
        "id": str(__import__('uuid').uuid4()),
        "to": to_email,
        "tenant_id": tenant.get("id", ""),
        "tenant_name": tenant.get("full_name", ""),
        "property": prop_addr,
        "room": room_num,
        "due_day": due_day,
        "type": reminder_type,
        "subject": subject,
        "message": message,
        "status": result.get("status", "error"),
        "provider_id": result.get("id"),
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.email_reminders.insert_one(record)

