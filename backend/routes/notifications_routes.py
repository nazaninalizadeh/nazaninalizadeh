"""Notification Routes - includes late payment alerts from monthly status."""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Notifications"])

MONTH_NAMES = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


@router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = []
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    today_day = int(now.strftime("%d"))
    current_month = now.month
    current_year = now.year

    # Late payment notifications from monthly status system
    tenants_with_rooms = await db.tenants.find({"room_id": {"$ne": ""}}, {"_id": 0}).to_list(1000)
    month_start = now.strftime("%Y-%m-01")
    month_end = f"{now.year + 1}-01-01" if now.month == 12 else f"{now.year}-{now.month + 1:02d}-01"

    for t in tenants_with_rooms:
        due_day = t.get("payment_due_day", 5)

        # Check manual override
        override = await db.monthly_status.find_one(
            {"tenant_id": t["id"], "month": current_month, "year": current_year}, {"_id": 0}
        )
        if override and override.get("status") == "paid":
            continue

        if override and override.get("status") == "late":
            is_late = True
        elif override:
            is_late = override.get("status") == "late"
        else:
            # Check payments
            payments = await db.payments.find(
                {"tenant_id": t["id"], "payment_date": {"$gte": month_start, "$lt": month_end}}, {"_id": 0}
            ).to_list(1)
            if payments:
                continue
            is_late = today_day > due_day

        if is_late:
            prop_addr = ""
            room_num = ""
            if t.get("property_id"):
                prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
                prop_addr = prop.get("address", "") if prop else ""
            if t.get("room_id"):
                room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
                room_num = room.get("room_number", "") if room else ""

            notifications.append({
                "type": "late_payment",
                "severity": "high",
                "title": f"Pagamento in ritardo: {t['full_name']}",
                "message": f"{MONTH_NAMES[current_month]} {current_year} - Scadenza giorno {due_day} - {prop_addr} Stanza {room_num}",
                "tenant_id": t["id"],
                "date": today_str,
                "month": current_month,
                "year": current_year,
                "property_address": prop_addr,
                "room_number": room_num,
            })

    # Expiring contracts
    next_month = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    expiring = await db.contracts.find({"status": "active", "end_date": {"$lte": next_month}}, {"_id": 0}).to_list(100)
    for c in expiring:
        notifications.append({
            "type": "contract_expiry", "severity": "medium",
            "title": f"Contratto in scadenza: {c.get('tenant_name', '')}",
            "message": f"Contratto {c.get('contract_number', '')} scade il {c.get('end_date', '')}",
            "tenant_id": c.get("tenant_id", ""), "date": c.get("end_date", ""),
        })

    # Expiring passports (90 days)
    next_90 = (now + timedelta(days=90)).strftime("%Y-%m-%d")
    tenants_pp = await db.tenants.find({"passport_expiry_date": {"$lte": next_90, "$gte": today_str}}, {"_id": 0}).to_list(100)
    for t in tenants_pp:
        notifications.append({
            "type": "passport_expiry", "severity": "low",
            "title": f"Passaporto in scadenza: {t['full_name']}",
            "message": f"Passaporto scade il {t['passport_expiry_date']}",
            "tenant_id": t["id"], "date": t["passport_expiry_date"],
        })

    notifications.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", ""), 3))
    return notifications
