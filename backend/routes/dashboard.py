"""Dashboard Routes."""

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
    unpaid_invoices = await db.invoices.count_documents({"payment_status": {"$in": ["unpaid", "partial"]}})
    total_rooms = await db.rooms.count_documents({})
    occupied_rooms = await db.rooms.count_documents({"status": "occupied"})

    contracts_list = await db.contracts.find({"status": "active"}, {"_id": 0, "rent_amount": 1}).to_list(1000)
    total_monthly_income = sum(c.get("rent_amount", 0) for c in contracts_list)
    tenants_list = await db.tenants.find({}, {"_id": 0, "deposit_amount": 1, "total_paid": 1, "total_due": 1}).to_list(1000)
    total_deposits = sum(t.get("deposit_amount", 0) for t in tenants_list)
    total_collected = sum(t.get("total_paid", 0) for t in tenants_list)
    total_outstanding = sum(max(0, t.get("total_due", 0) - t.get("total_paid", 0)) for t in tenants_list)

    recent_payments = await db.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    for p in recent_payments:
        if p.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": p["tenant_id"]}, {"_id": 0})
            p["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            p["tenant_name"] = ""

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    overdue = await db.invoices.find({"payment_status": {"$in": ["unpaid", "partial"]}, "due_date": {"$lt": today}}, {"_id": 0}).to_list(20)

    return {
        "total_tenants": total_tenants,
        "total_landlords": total_landlords,
        "total_properties": total_properties,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": total_rooms - occupied_rooms,
        "active_contracts": active_contracts,
        "unpaid_invoices": unpaid_invoices,
        "total_monthly_income": total_monthly_income,
        "total_deposits": total_deposits,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "recent_payments": recent_payments,
        "overdue_invoices": overdue,
    }
