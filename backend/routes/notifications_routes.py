"""Notification Routes - includes late payment alerts + notification count for badge."""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Notifications"])

MONTH_NAMES = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


def _became_late_at(year: int, month: int, due_day: int) -> datetime:
    """When a tenant transitions to LATE: 00:00 UTC of the day AFTER the due day."""
    day = max(1, min(due_day + 1, 28))  # clamp; due_day+1 should never overflow month for typical due_days
    return datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)


async def _get_last_viewed_at(admin_id: str) -> datetime:
    rec = await db.notification_views.find_one({"admin_id": admin_id}, {"_id": 0, "last_viewed_at": 1})
    if not rec or not rec.get("last_viewed_at"):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    raw = rec["last_viewed_at"]
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


@router.get("/notifications/count")
async def get_notification_count(user: dict = Depends(get_current_user)):
    """Quick count of UNSEEN late-tenant notifications for the badge.
    A late tenant is "unseen" if it became late AFTER the admin last opened
    the Notifiche page. Optimized: 3 bulk queries instead of N+1 per tenant.
    """
    now = datetime.now(timezone.utc)
    today_day = int(now.strftime("%d"))
    current_month = now.month
    current_year = now.year
    month_start = now.strftime("%Y-%m-01")
    month_end = f"{now.year + 1}-01-01" if now.month == 12 else f"{now.year}-{now.month + 1:02d}-01"

    last_viewed = await _get_last_viewed_at(user["id"])

    tenants_with_rooms = await db.tenants.find(
        {"room_id": {"$ne": ""}},
        {"_id": 0, "id": 1, "payment_due_day": 1},
    ).to_list(10000)
    if not tenants_with_rooms:
        return {"count": 0}

    tenant_ids = [t["id"] for t in tenants_with_rooms]

    overrides = await db.monthly_status.find(
        {"tenant_id": {"$in": tenant_ids}, "month": current_month, "year": current_year},
        {"_id": 0, "tenant_id": 1, "status": 1},
    ).to_list(10000)
    overrides_by_tid = {o["tenant_id"]: o.get("status") for o in overrides}

    payments = await db.payments.find(
        {"tenant_id": {"$in": tenant_ids}, "payment_date": {"$gte": month_start, "$lt": month_end}},
        {"_id": 0, "tenant_id": 1},
    ).to_list(100000)
    paid_tenant_ids = {p["tenant_id"] for p in payments}

    count = 0
    for t in tenants_with_rooms:
        status = overrides_by_tid.get(t["id"])
        if status == "paid":
            continue
        due_day = t.get("payment_due_day", 5)
        is_late = (status == "late") or (
            status not in ("not_paid",) and t["id"] not in paid_tenant_ids and today_day > due_day
        )
        if not is_late:
            continue
        # Only count if it became late AFTER the admin last viewed notifications.
        became_late = _became_late_at(current_year, current_month, due_day)
        if became_late > last_viewed:
            count += 1
    return {"count": count}


@router.post("/notifications/mark-seen")
async def mark_notifications_seen(user: dict = Depends(get_current_user)):
    """Called by the frontend when the Notifiche page is opened.
    Records "last_viewed_at = now" for the current admin so the badge resets to 0.
    A new late-tenant emerging after this timestamp will bring the badge back.
    """
    now = datetime.now(timezone.utc)
    await db.notification_views.update_one(
        {"admin_id": user["id"]},
        {"$set": {"admin_id": user["id"], "last_viewed_at": now.isoformat()}},
        upsert=True,
    )
    return {"message": "Notifiche segnate come viste", "viewed_at": now.isoformat()}


@router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = []
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    today_day = int(now.strftime("%d"))
    current_month = now.month
    current_year = now.year
    month_start = now.strftime("%Y-%m-01")
    month_end = f"{now.year + 1}-01-01" if now.month == 12 else f"{now.year}-{now.month + 1:02d}-01"

    # Late payment notifications
    tenants_with_rooms = await db.tenants.find({"room_id": {"$ne": ""}}, {"_id": 0}).to_list(1000)
    for t in tenants_with_rooms:
        due_day = t.get("payment_due_day", 5)
        override = await db.monthly_status.find_one(
            {"tenant_id": t["id"], "month": current_month, "year": current_year}, {"_id": 0}
        )
        if override and override.get("status") == "paid":
            continue

        is_late = False
        if override and override.get("status") == "late":
            is_late = True
        else:
            payments = await db.payments.find(
                {"tenant_id": t["id"], "payment_date": {"$gte": month_start, "$lt": month_end}}, {"_id": 0}
            ).to_list(1)
            if not payments and today_day > due_day:
                is_late = True

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
                "type": "late_payment", "severity": "high",
                "title": f"Pagamento in ritardo: {t['full_name']}",
                "message": f"{MONTH_NAMES[current_month]} {current_year} - Scadenza giorno {due_day} - {prop_addr} Stanza {room_num}",
                "tenant_id": t["id"], "date": today_str,
            })

    # Expiring contracts (1 week before)
    next_week = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    expiring = await db.contracts.find({"status": "active", "end_date": {"$lte": next_week, "$gte": today_str}}, {"_id": 0}).to_list(100)
    for c in expiring:
        notifications.append({
            "type": "contract_expiry", "severity": "medium",
            "title": f"Contratto in scadenza: {c.get('tenant_name', '')}",
            "message": f"Contratto scade il {c.get('end_date', '')}",
            "tenant_id": c.get("tenant_id", ""), "date": c.get("end_date", ""),
        })

    # Expiring passports
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


@router.post("/reminders/check")
async def trigger_reminder_check(user: dict = Depends(get_current_user)):
    """Manually trigger email reminder check."""
    from services.email_reminders import check_and_send_reminders
    await check_and_send_reminders()
    return {"message": "Reminder check completato"}
