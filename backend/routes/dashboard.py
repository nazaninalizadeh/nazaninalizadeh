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

    # Count tenants who paid this month vs not
    occupied_tenants = await db.tenants.find({"room_id": {"$ne": ""}}, {"_id": 0, "id": 1}).to_list(1000)
    paid_tenant_ids = set(p.get("tenant_id") for p in month_payments)
    tenants_paid = sum(1 for t in occupied_tenants if t["id"] in paid_tenant_ids)
    tenants_not_paid = len(occupied_tenants) - tenants_paid

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
        "recent_payments": recent_payments,
        "current_month": now.strftime("%B %Y"),
    }
