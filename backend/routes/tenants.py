"""Tenant Routes."""

from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import TenantCreate

router = APIRouter(prefix="/api", tags=["Tenants"])


@router.post("/tenants")
async def create_tenant(tenant: TenantCreate, user: dict = Depends(get_current_user)):
    tenant_dict = tenant.model_dump()
    tenant_dict["id"] = str(uuid.uuid4())
    tenant_dict["total_paid"] = 0.0
    tenant_dict["total_due"] = 0.0
    tenant_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    tenant_dict["created_by"] = user.get("email", "")
    await db.tenants.insert_one(tenant_dict)
    t = await db.tenants.find_one({"id": tenant_dict["id"]}, {"_id": 0})
    t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
    t["current_property"] = t.get("property_id", "")
    return t


@router.get("/tenants")
async def get_tenants(user: dict = Depends(get_current_user)):
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    for t in tenants:
        t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
        t["current_property"] = t.get("property_id", "")
        if t.get("room_id"):
            room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
            t["room_number"] = room.get("room_number", "") if room else ""
        else:
            t["room_number"] = ""
        if t.get("property_id"):
            prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
            t["property_address"] = prop.get("address", "") if prop else ""
        else:
            t["property_address"] = ""
    return tenants


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    t = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
    t["current_property"] = t.get("property_id", "")
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
    await db.tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    if update_dict.get("room_id") and update_dict["room_id"] != existing.get("room_id", ""):
        if existing.get("room_id"):
            await db.rooms.update_one({"id": existing["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
        await db.rooms.update_one({"id": update_dict["room_id"]}, {"$set": {"status": "occupied", "tenant_id": tenant_id}})
    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    updated["remaining_balance"] = updated.get("total_due", 0) - updated.get("total_paid", 0)
    updated["current_property"] = updated.get("property_id", "")
    return updated


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.get("room_id"):
        await db.rooms.update_one({"id": tenant["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
    await db.tenants.delete_one({"id": tenant_id})
    return {"message": "Tenant deleted"}
