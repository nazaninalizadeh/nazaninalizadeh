"""Landlord Routes."""

from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import LandlordCreate

router = APIRouter(prefix="/api", tags=["Landlords"])


@router.post("/landlords")
async def create_landlord(landlord: LandlordCreate, user: dict = Depends(get_current_user)):
    d = landlord.model_dump()
    d["id"] = str(uuid.uuid4())
    d["properties_count"] = 0
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.landlords.insert_one(d)
    return {**{k: v for k, v in d.items() if k != "_id"}, "properties_count": 0}


@router.get("/landlords")
async def get_landlords(user: dict = Depends(get_current_user)):
    landlords = await db.landlords.find({}, {"_id": 0}).to_list(1000)
    for ll in landlords:
        props = await db.properties.find({"landlord_id": ll["id"]}, {"_id": 0}).to_list(100)
        ll["properties_count"] = len(props)
        total_rooms = 0
        occupied_rooms = 0
        for p in props:
            rooms = await db.rooms.find({"property_id": p["id"]}, {"_id": 0}).to_list(100)
            total_rooms += len(rooms)
            occupied_rooms += sum(1 for r in rooms if r.get("status") == "occupied")
        ll["total_rooms"] = total_rooms
        ll["occupied_rooms"] = occupied_rooms
        ll["vacant_rooms"] = total_rooms - occupied_rooms
    return landlords


@router.get("/landlords/{landlord_id}")
async def get_landlord(landlord_id: str, user: dict = Depends(get_current_user)):
    ll = await db.landlords.find_one({"id": landlord_id}, {"_id": 0})
    if not ll:
        raise HTTPException(status_code=404, detail="Landlord not found")
    props = await db.properties.find({"landlord_id": landlord_id}, {"_id": 0}).to_list(100)
    ll["properties_count"] = len(props)
    ll["properties"] = props
    total_rooms = 0
    occupied_rooms = 0
    total_income = 0.0
    for p in props:
        rooms = await db.rooms.find({"property_id": p["id"]}, {"_id": 0}).to_list(100)
        p["rooms"] = rooms
        total_rooms += len(rooms)
        occ = sum(1 for r in rooms if r.get("status") == "occupied")
        occupied_rooms += occ
        p["occupied_rooms"] = occ
        p["vacant_rooms"] = len(rooms) - occ
        total_income += p.get("rental_amount", 0)
    ll["total_rooms"] = total_rooms
    ll["occupied_rooms"] = occupied_rooms
    ll["vacant_rooms"] = total_rooms - occupied_rooms
    ll["total_monthly_income"] = total_income
    docs = await db.documents.find({"owner_id": landlord_id}, {"_id": 0}).to_list(50)
    ll["documents"] = docs
    return ll


@router.put("/landlords/{landlord_id}")
async def update_landlord(landlord_id: str, landlord_update: LandlordCreate, user: dict = Depends(get_current_user)):
    existing = await db.landlords.find_one({"id": landlord_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Landlord not found")
    await db.landlords.update_one({"id": landlord_id}, {"$set": landlord_update.model_dump()})
    updated = await db.landlords.find_one({"id": landlord_id}, {"_id": 0})
    updated["properties_count"] = await db.properties.count_documents({"landlord_id": landlord_id})
    return updated


@router.delete("/landlords/{landlord_id}")
async def delete_landlord(landlord_id: str, user: dict = Depends(get_current_user)):
    result = await db.landlords.delete_one({"id": landlord_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Landlord not found")
    return {"message": "Landlord deleted"}
