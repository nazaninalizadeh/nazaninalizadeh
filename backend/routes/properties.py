"""Property Routes."""

from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import PropertyCreate

router = APIRouter(prefix="/api", tags=["Properties"])


@router.post("/properties")
async def create_property(property_data: PropertyCreate, user: dict = Depends(get_current_user)):
    landlord = await db.landlords.find_one({"id": property_data.landlord_id}, {"_id": 0})
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    d = property_data.model_dump()
    d["id"] = str(uuid.uuid4())
    d["landlord_name"] = landlord["full_name"]
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.properties.insert_one(d)
    d.pop("_id", None)
    d["occupancy_status"] = "vacant"
    d["current_tenants_count"] = 0
    return d


@router.get("/properties")
async def get_properties(user: dict = Depends(get_current_user)):
    properties = await db.properties.find({}, {"_id": 0}).to_list(1000)
    for p in properties:
        rooms = await db.rooms.find({"property_id": p["id"]}, {"_id": 0}).to_list(100)
        occ = sum(1 for r in rooms if r.get("status") == "occupied")
        p["current_tenants_count"] = occ
        p["occupancy_status"] = "occupied" if occ > 0 else "vacant"
        p["total_rooms_count"] = len(rooms)
        p["occupied_rooms_count"] = occ
        p["vacant_rooms_count"] = len(rooms) - occ
    return properties


@router.get("/properties/{property_id}")
async def get_property(property_id: str, user: dict = Depends(get_current_user)):
    p = await db.properties.find_one({"id": property_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    rooms = await db.rooms.find({"property_id": property_id}, {"_id": 0}).to_list(100)
    for r in rooms:
        if r.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": r["tenant_id"]}, {"_id": 0})
            r["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            r["tenant_name"] = ""
    p["rooms"] = rooms
    occ = sum(1 for r in rooms if r.get("status") == "occupied")
    p["current_tenants_count"] = occ
    p["occupancy_status"] = "occupied" if occ > 0 else "vacant"
    p["total_rooms_count"] = len(rooms)
    p["occupied_rooms_count"] = occ
    p["vacant_rooms_count"] = len(rooms) - occ
    tenants = await db.tenants.find({"property_id": property_id}, {"_id": 0}).to_list(100)
    for t in tenants:
        t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
    p["tenants"] = tenants
    return p


@router.put("/properties/{property_id}")
async def update_property(property_id: str, property_update: PropertyCreate, user: dict = Depends(get_current_user)):
    existing = await db.properties.find_one({"id": property_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Property not found")
    landlord = await db.landlords.find_one({"id": property_update.landlord_id}, {"_id": 0})
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    update_dict = property_update.model_dump()
    update_dict["landlord_name"] = landlord["full_name"]
    await db.properties.update_one({"id": property_id}, {"$set": update_dict})
    updated = await db.properties.find_one({"id": property_id}, {"_id": 0})
    rooms = await db.rooms.find({"property_id": property_id}, {"_id": 0}).to_list(100)
    occ = sum(1 for r in rooms if r.get("status") == "occupied")
    updated["current_tenants_count"] = occ
    updated["occupancy_status"] = "occupied" if occ > 0 else "vacant"
    return updated


@router.delete("/properties/{property_id}")
async def delete_property(property_id: str, user: dict = Depends(get_current_user)):
    result = await db.properties.delete_one({"id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    await db.rooms.delete_many({"property_id": property_id})
    return {"message": "Property deleted"}
