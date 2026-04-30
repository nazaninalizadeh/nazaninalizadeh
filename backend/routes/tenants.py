"""Tenant Routes - 3 payment statuses: paid / not_paid / late."""

from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import TenantCreate

router = APIRouter(prefix="/api", tags=["Tenants"])


def _current_month_range():
    now = datetime.now(timezone.utc)
    start = now.strftime("%Y-%m-01")
    if now.month == 12:
        end = f"{now.year + 1}-01-01"
    else:
        end = f"{now.year}-{now.month + 1:02d}-01"
    return start, end


async def _enrich_tenant(t: dict) -> dict:
    """Add payment status (paid/not_paid/late), property/room info."""
    start, end = _current_month_range()
    now = datetime.now(timezone.utc)
    today = int(now.strftime("%d"))
    current_month = now.month
    current_year = now.year

    due_day = t.get("payment_due_day", 5)

    # 1. Check manual override first
    override = await db.monthly_status.find_one(
        {"tenant_id": t["id"], "month": current_month, "year": current_year},
        {"_id": 0}
    )
    if override:
        method_map = {"contanti": "Contanti", "cash": "Contanti", "bonifico": "Bonifico", "bank_transfer": "Bonifico", "carta": "Carta"}
        raw = override.get("payment_method", "")
        t["payment_status"] = override["status"]
        t["month_paid_amount"] = override.get("amount", 0)
        t["month_payment_method"] = method_map.get(raw, raw.capitalize() if raw else "")
    else:
        # 2. Check actual payments
        current_payments = await db.payments.find(
            {"tenant_id": t["id"], "payment_date": {"$gte": start, "$lt": end}}
        , {"_id": 0}).to_list(10)

        if current_payments:
            total_paid_month = sum(p.get("amount", 0) for p in current_payments)
            methods = list(set(p.get("payment_method", "") for p in current_payments))
            method_map = {"contanti": "Contanti", "cash": "Contanti", "bonifico": "Bonifico", "bank_transfer": "Bonifico", "carta": "Carta"}
            raw = methods[0] if len(methods) == 1 else ", ".join(methods)
            t["payment_status"] = "paid"
            t["month_paid_amount"] = total_paid_month
            t["month_payment_method"] = method_map.get(raw, raw.capitalize() if raw else "")
        else:
            # 3. Auto-determine based on due day
            if today > due_day and t.get("room_id"):
                t["payment_status"] = "late"
            else:
                t["payment_status"] = "not_paid"
            t["month_paid_amount"] = 0
            t["month_payment_method"] = ""

    # Room info
    if t.get("room_id"):
        room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
        t["room_number"] = room.get("room_number", "") if room else ""
        t["room_type"] = room.get("room_type", "") if room else ""
        t["room_rent"] = room.get("monthly_rent", 0) if room else 0
    else:
        t["room_number"] = ""
        t["room_type"] = ""
        t["room_rent"] = 0

    # Property info
    if t.get("property_id"):
        prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
        t["property_address"] = prop.get("address", "") if prop else ""
    else:
        t["property_address"] = ""

    return t


@router.post("/tenants")
async def create_tenant(tenant: TenantCreate, user: dict = Depends(get_current_user)):
    tenant_dict = tenant.model_dump()
    tenant_dict["id"] = str(uuid.uuid4())
    tenant_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    tenant_dict["created_by"] = user.get("email", "")
    await db.tenants.insert_one(tenant_dict)
    t = await db.tenants.find_one({"id": tenant_dict["id"]}, {"_id": 0})
    return await _enrich_tenant(t)


@router.get("/tenants")
async def get_tenants(status: str = "", user: dict = Depends(get_current_user)):
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    for t in tenants:
        await _enrich_tenant(t)
    if status and status in ("paid", "not_paid", "late"):
        tenants = [t for t in tenants if t.get("payment_status") == status]
    return tenants


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    t = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await _enrich_tenant(t)
    docs = await db.documents.find({"owner_id": tenant_id}, {"_id": 0}).to_list(50)
    t["documents"] = docs
    payments = await db.payments.find({"tenant_id": tenant_id}, {"_id": 0}).sort("payment_date", -1).to_list(100)
    t["payments"] = payments
    invoices = await db.invoices.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    t["invoices"] = invoices
    contracts = await db.contracts.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    t["contracts"] = contracts
    if t.get("room_id"):
        room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
        t["room_info"] = room
    if t.get("property_id"):
        prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
        t["property_info"] = prop
    return t


@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, tenant_update: TenantCreate, user: dict = Depends(get_current_user)):
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    update_dict = tenant_update.model_dump()
    if existing.get("deposit_amount", 0) > 0 and update_dict.get("deposit_amount", 0) < existing["deposit_amount"]:
        update_dict["deposit_amount"] = existing["deposit_amount"]
    await db.tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    if update_dict.get("room_id") and update_dict["room_id"] != existing.get("room_id", ""):
        if existing.get("room_id"):
            await db.rooms.update_one({"id": existing["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
        await db.rooms.update_one({"id": update_dict["room_id"]}, {"$set": {"status": "occupied", "tenant_id": tenant_id}})
    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    return await _enrich_tenant(updated)


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.get("room_id"):
        await db.rooms.update_one({"id": tenant["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
    # Cascade delete related records so orphans don't linger
    await db.hospitality_records.delete_many({"tenant_id": tenant_id})
    await db.monthly_status.delete_many({"tenant_id": tenant_id})
    await db.tenants.delete_one({"id": tenant_id})
    return {"message": "Tenant deleted"}
