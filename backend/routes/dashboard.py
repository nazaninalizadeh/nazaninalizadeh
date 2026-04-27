"""Dashboard Routes - Simplified: no deposit-based balance calculations."""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_tenants = await db.tenants.count_documents({})
    total_landlords = await db.landlords.count_documents({})
    total_properties = await db.properties.count_documents({})
    active_contracts = await db.contracts.count_documents({"status": "active"})
    total_rooms = await db.rooms.count_documents({})
    occupied_rooms = await db.rooms.count_documents({"status": "occupied"})

    # Current month payment stats
    now = datetime.now(timezone.utc)
    month_start = now.strftime("%Y-%m-01")
    if now.month == 12:
        month_end = f"{now.year + 1}-01-01"
    else:
        month_end = f"{now.year}-{now.month + 1:02d}-01"

    month_payments = await db.payments.find(
        {"payment_date": {"$gte": month_start, "$lt": month_end}}, {"_id": 0}
    ).to_list(5000)
    month_collected = sum(p.get("amount", 0) for p in month_payments)
    month_payment_count = len(month_payments)

    # Count tenants: paid, not_paid, late (respecting manual overrides)
    occupied_tenants = await db.tenants.find({"room_id": {"$ne": ""}}, {"_id": 0, "id": 1, "payment_due_day": 1}).to_list(1000)
    paid_tenant_ids = set(p.get("tenant_id") for p in month_payments)
    today_day = int(now.strftime("%d"))
    current_month = now.month
    current_year = now.year
    tenants_paid = 0
    tenants_not_paid = 0
    tenants_late = 0
    late_details = []

    for t in occupied_tenants:
        # Check manual override first
        override = await db.monthly_status.find_one(
            {"tenant_id": t["id"], "month": current_month, "year": current_year}, {"_id": 0}
        )
        if override:
            s = override.get("status", "not_paid")
        elif t["id"] in paid_tenant_ids:
            s = "paid"
        elif today_day > t.get("payment_due_day", 5):
            s = "late"
        else:
            s = "not_paid"

        if s == "paid":
            tenants_paid += 1
        elif s == "late":
            # Always append details so list length == count (single source of truth)
            tenant_doc = await db.tenants.find_one({"id": t["id"]}, {"_id": 0}) or {}
            prop_addr = ""
            room_num = ""
            if tenant_doc.get("property_id"):
                prop = await db.properties.find_one({"id": tenant_doc["property_id"]}, {"_id": 0})
                prop_addr = prop.get("address", "") if prop else ""
            if tenant_doc.get("room_id"):
                room = await db.rooms.find_one({"id": tenant_doc["room_id"]}, {"_id": 0})
                room_num = room.get("room_number", "") if room else ""
            late_details.append({
                "tenant_id": t["id"],
                "tenant_name": tenant_doc.get("full_name", "") or "—",
                "property_address": prop_addr,
                "room_number": room_num,
                "due_day": t.get("payment_due_day", 5),
            })
        else:
            tenants_not_paid += 1

    # Count is ALWAYS derived from list length — guaranteed consistency
    tenants_late = len(late_details)

    # Total deposits (constant, just for info)
    tenants_list = await db.tenants.find({}, {"_id": 0, "deposit_amount": 1}).to_list(1000)
    total_deposits = sum(t.get("deposit_amount", 0) for t in tenants_list)

    # Recent payments
    recent_payments = await db.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    for p in recent_payments:
        if p.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": p["tenant_id"]}, {"_id": 0})
            p["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            p["tenant_name"] = ""

    return {
        "total_tenants": total_tenants,
        "total_landlords": total_landlords,
        "total_properties": total_properties,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": total_rooms - occupied_rooms,
        "active_contracts": active_contracts,
        "total_deposits": total_deposits,
        "month_collected": month_collected,
        "month_payment_count": month_payment_count,
        "tenants_paid": tenants_paid,
        "tenants_not_paid": tenants_not_paid,
        "tenants_late": tenants_late,
        "late_details": late_details,
        "recent_payments": recent_payments,
        "current_month": now.strftime("%B %Y"),
    }
