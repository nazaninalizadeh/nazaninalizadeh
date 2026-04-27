"""Email Reminder Service - mocked but structured for Resend/SendGrid."""

import logging
from datetime import datetime, timezone, timedelta
from database import db

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
            # 1 week before due date
            await _send_reminder(tenant, prop_addr, room_num, due_day, "pre_reminder",
                f"Gentile {tenant['full_name']}, ricordiamo che il pagamento dell'affitto "
                f"per {prop_addr} (Stanza {room_num}) scade il giorno {due_day} "
                f"di {MONTH_NAMES[current_month]}. La preghiamo di provvedere entro la scadenza.")

        elif days_after_due == 1:
            # 1 day after due date
            await _send_reminder(tenant, prop_addr, room_num, due_day, "late_warning",
                f"Gentile {tenant['full_name']}, il pagamento dell'affitto per {prop_addr} "
                f"(Stanza {room_num}) risulta scaduto dal giorno {due_day}/{current_month:02d}/{current_year}. "
                f"La preghiamo di provvedere al pagamento il prima possibile.")

        elif days_after_due == 7:
            # 1 week after due date
            await _send_reminder(tenant, prop_addr, room_num, due_day, "second_reminder",
                f"SECONDO AVVISO - Gentile {tenant['full_name']}, il pagamento dell'affitto "
                f"per {prop_addr} (Stanza {room_num}) risulta ancora non pagato. "
                f"Scadenza originale: {due_day}/{current_month:02d}/{current_year}. "
                f"La preghiamo di contattarci urgentemente.")


async def _send_reminder(tenant: dict, prop_addr: str, room_num: str, due_day: int, reminder_type: str, message: str):
    """Send email reminder (MOCKED - logs to console, ready for Resend/SendGrid)."""
    email_data = {
        "to": tenant.get("email", ""),
        "tenant_name": tenant.get("full_name", ""),
        "property": prop_addr,
        "room": room_num,
        "due_day": due_day,
        "type": reminder_type,
        "message": message,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    # Log the email (MOCKED)
    logger.info(f"""
{'='*60}
EMAIL REMINDER [{reminder_type.upper()}]
To: {email_data['to']}
Tenant: {email_data['tenant_name']}
Property: {prop_addr} - Room {room_num}
Due Day: {due_day}
{'='*60}
{message}
{'='*60}
""")

    # Save reminder record
    email_data["id"] = str(__import__('uuid').uuid4())
    email_data["tenant_id"] = tenant.get("id", "")
    email_data["status"] = "sent_mock"
    await db.email_reminders.insert_one(email_data)

    # TODO: Replace with real email service
    # from resend import Emails
    # Emails.send({
    #     "from": "noreply@consulenze-immobiliari.it",
    #     "to": email_data["to"],
    #     "subject": f"Promemoria Affitto - {prop_addr}",
    #     "html": f"<p>{message}</p>"
    # })
