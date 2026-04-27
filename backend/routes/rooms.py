"""Room Routes."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
import uuid
from datetime import datetime, timezone
import aiofiles
from pathlib import Path

from database import db
from auth import get_current_user
from models.schemas import RoomCreate

router = APIRouter(prefix="/api", tags=["Rooms"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

# Image upload security
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


async def _read_and_validate_image(file: UploadFile) -> tuple[bytes, str]:
    """Validate uploaded image file. Returns (content, ext) or raises HTTPException."""
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="Nome file non valido.")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa JPG, PNG o WEBP.")
    if file.content_type and file.content_type.lower() not in ALLOWED_IMAGE_MIMES:
        raise HTTPException(status_code=400, detail="Tipo MIME non valido. Usa JPG, PNG o WEBP.")
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File vuoto.")
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File troppo grande. Massimo 5MB.")
    return content, ext


@router.post("/rooms")
async def create_room(room: RoomCreate, user: dict = Depends(get_current_user)):
    prop = await db.properties.find_one({"id": room.property_id})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    d = room.model_dump()
    d["id"] = str(uuid.uuid4())
    d["status"] = "available"
    d["tenant_id"] = ""
    d["images"] = []
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.rooms.insert_one(d)
    d.pop("_id", None)
    d["tenant_name"] = ""
    d["property_address"] = prop.get("address", "")
    return d


@router.get("/rooms")
async def get_rooms(property_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"property_id": property_id} if property_id else {}
    rooms = await db.rooms.find(query, {"_id": 0}).to_list(1000)
    for r in rooms:
        if r.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": r["tenant_id"]}, {"_id": 0})
            r["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            r["tenant_name"] = ""
        prop = await db.properties.find_one({"id": r["property_id"]}, {"_id": 0})
        r["property_address"] = prop.get("address", "") if prop else ""
    return rooms


@router.get("/rooms/{room_id}")
async def get_room(room_id: str, user: dict = Depends(get_current_user)):
    r = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")
    if r.get("tenant_id"):
        tenant = await db.tenants.find_one({"id": r["tenant_id"]}, {"_id": 0})
        r["tenant_name"] = tenant.get("full_name", "") if tenant else ""
    else:
        r["tenant_name"] = ""
    return r


@router.put("/rooms/{room_id}")
async def update_room(room_id: str, room_update: RoomCreate, user: dict = Depends(get_current_user)):
    existing = await db.rooms.find_one({"id": room_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Room not found")
    await db.rooms.update_one({"id": room_id}, {"$set": room_update.model_dump()})
    updated = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    return updated


@router.delete("/rooms/{room_id}")
async def delete_room(room_id: str, user: dict = Depends(get_current_user)):
    result = await db.rooms.delete_one({"id": room_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted"}


@router.post("/rooms/{room_id}/assign")
async def assign_tenant_to_room(room_id: str, tenant_id: str = Form(...), user: dict = Depends(get_current_user)):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.get("room_id"):
        await db.rooms.update_one({"id": tenant["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
    await db.rooms.update_one({"id": room_id}, {"$set": {"status": "occupied", "tenant_id": tenant_id}})
    await db.tenants.update_one({"id": tenant_id}, {"$set": {"room_id": room_id, "property_id": room["property_id"]}})
    return {"message": "Tenant assigned to room"}


@router.post("/rooms/{room_id}/unassign")
async def unassign_tenant_from_room(room_id: str, user: dict = Depends(get_current_user)):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.get("tenant_id"):
        await db.tenants.update_one({"id": room["tenant_id"]}, {"$set": {"room_id": "", "property_id": ""}})
    await db.rooms.update_one({"id": room_id}, {"$set": {"status": "available", "tenant_id": ""}})
    return {"message": "Tenant unassigned"}


@router.post("/rooms/{room_id}/images")
async def upload_room_image(room_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    content, ext = await _read_and_validate_image(file)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "rooms").mkdir(exist_ok=True)
    filename = f"{room_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / "rooms" / filename
    async with aiofiles.open(str(filepath), "wb") as f:
        await f.write(content)
    url = f"/uploads/rooms/{filename}"
    await db.rooms.update_one({"id": room_id}, {"$push": {"images": url}})
    return {"url": url}


@router.post("/properties/{property_id}/images")
async def upload_property_image(property_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    prop = await db.properties.find_one({"id": property_id})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    content, ext = await _read_and_validate_image(file)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "properties").mkdir(exist_ok=True)
    filename = f"{property_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / "properties" / filename
    async with aiofiles.open(str(filepath), "wb") as f:
        await f.write(content)
    url = f"/uploads/properties/{filename}"
    await db.properties.update_one({"id": property_id}, {"$push": {"images": url}})
    return {"url": url}


@router.delete("/properties/{property_id}/images")
async def delete_property_image(property_id: str, url: str = "", user: dict = Depends(get_current_user)):
    if not url:
        raise HTTPException(status_code=400, detail="URL immagine mancante.")
    await db.properties.update_one({"id": property_id}, {"$pull": {"images": url}})
    return {"message": "Immagine rimossa"}


@router.delete("/rooms/{room_id}/images")
async def delete_room_image(room_id: str, url: str = "", user: dict = Depends(get_current_user)):
    if not url:
        raise HTTPException(status_code=400, detail="URL immagine mancante.")
    await db.rooms.update_one({"id": room_id}, {"$pull": {"images": url}})
    return {"message": "Immagine rimossa"}


@router.get("/occupancy-overview")
async def get_occupancy_overview(user: dict = Depends(get_current_user)):
    """Current month payment status per property/room/tenant."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    month_start = now.strftime("%Y-%m-01")
    month_end = f"{now.year + 1}-01-01" if now.month == 12 else f"{now.year}-{now.month + 1:02d}-01"

    properties = await db.properties.find({}, {"_id": 0}).to_list(500)
    result = []
    for prop in properties:
        rooms = await db.rooms.find({"property_id": prop["id"]}, {"_id": 0}).to_list(200)
        room_list = []
        for room in rooms:
            room_data = {
                "id": room["id"],
                "room_number": room.get("room_number", ""),
                "room_type": room.get("room_type", ""),
                "status": room.get("status", "available"),
                "tenant_id": room.get("tenant_id", ""),
                "tenant_name": "",
                "payment_status": "none",
                "payment_amount": 0,
                "payment_method": "",
            }
            if room.get("tenant_id"):
                tenant = await db.tenants.find_one({"id": room["tenant_id"]}, {"_id": 0})
                if tenant:
                    room_data["tenant_name"] = tenant.get("full_name", "")
                    # Check CURRENT MONTH payments only
                    month_payments = await db.payments.find(
                        {"tenant_id": room["tenant_id"], "payment_date": {"$gte": month_start, "$lt": month_end}}
                    , {"_id": 0}).to_list(10)
                    if month_payments:
                        total = sum(p.get("amount", 0) for p in month_payments)
                        methods = list(set(p.get("payment_method", "") for p in month_payments))
                        raw = methods[0] if len(methods) == 1 else ", ".join(methods)
                        method_map = {"contanti": "Contanti", "cash": "Contanti", "bonifico": "Bonifico", "bank_transfer": "Bonifico", "carta": "Carta"}
                        room_data["payment_status"] = "paid"
                        room_data["payment_amount"] = total
                        room_data["payment_method"] = method_map.get(raw, raw.capitalize() if raw else "")
                    else:
                        room_data["payment_status"] = "not_paid"
            room_list.append(room_data)
        room_list.sort(key=lambda r: r["room_number"])
        occupied = sum(1 for r in room_list if r["status"] == "occupied")
        result.append({
            "id": prop["id"],
            "property_code": prop.get("property_code", ""),
            "address": prop.get("address", ""),
            "landlord_name": prop.get("landlord_name", ""),
            "total_rooms": len(room_list),
            "occupied_rooms": occupied,
            "vacant_rooms": len(room_list) - occupied,
            "rooms": room_list,
        })
    return result
