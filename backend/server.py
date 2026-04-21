from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import asyncio
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch, cm
import base64
import aiofiles
import json

from database import db, client
from auth import auth_router, get_current_user, seed_admins, ALLOWED_ADMINS

app = FastAPI()
api_router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "documents").mkdir(exist_ok=True)
(UPLOAD_DIR / "rooms").mkdir(exist_ok=True)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ============ Models ============

class TenantCreate(BaseModel):
    full_name: str
    codice_fiscale: Optional[str] = ""
    passport_number: str
    nationality: str
    date_of_birth: str
    passport_issue_date: str
    passport_expiry_date: str
    id_type: Optional[str] = ""
    id_number: Optional[str] = ""
    phone: str
    email: EmailStr
    whatsapp: str
    address: str
    occupation: str
    notes: Optional[str] = ""
    deposit_amount: float = 0.0
    property_id: Optional[str] = ""
    room_id: Optional[str] = ""

class LandlordCreate(BaseModel):
    full_name: str
    codice_fiscale: Optional[str] = ""
    phone: str
    email: EmailStr
    whatsapp: str
    id_type: Optional[str] = ""
    id_number: str
    bank_details: str
    notes: Optional[str] = ""

class PropertyCreate(BaseModel):
    property_code: str
    address: str
    property_type: str
    number_of_rooms: int
    capacity: int
    landlord_id: str
    rental_amount: float
    deposit_amount: float
    additional_charges: Optional[str] = ""

class RoomCreate(BaseModel):
    property_id: str
    room_number: str
    room_type: str  # single / double
    floor: Optional[str] = ""
    monthly_rent: float = 0.0
    description: Optional[str] = ""
    bill_responsible: Optional[str] = ""  # tenant_id or "landlord"

class ContractCreate(BaseModel):
    tenant_id: str
    property_id: str
    room_id: Optional[str] = ""
    start_date: str
    end_date: str
    rent_amount: float
    deposit_amount: float
    terms: str

class InvoiceCreate(BaseModel):
    tenant_id: str
    property_id: str
    contract_id: str
    invoice_type: str
    amount: float
    due_date: str
    description: str

class PaymentCreate(BaseModel):
    invoice_id: Optional[str] = ""
    tenant_id: str
    amount: float
    payment_method: str
    payment_date: str
    notes: Optional[str] = ""

# ============ Startup ============
@app.on_event("startup")
async def startup_event():
    await db.tenants.create_index("passport_number")
    await db.properties.create_index("property_code")
    await db.contracts.create_index("contract_number")
    await db.invoices.create_index("invoice_number")
    await db.rooms.create_index("property_id")
    await db.payments.create_index("tenant_id")
    await db.documents.create_index("owner_id")
    await seed_admins()

# ============ Tenant Routes ============
@api_router.post("/tenants")
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

@api_router.get("/tenants")
async def get_tenants(user: dict = Depends(get_current_user)):
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    for t in tenants:
        t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
        t["current_property"] = t.get("property_id", "")
        # Get room info
        if t.get("room_id"):
            room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
            t["room_number"] = room.get("room_number", "") if room else ""
        else:
            t["room_number"] = ""
        # Get property info
        if t.get("property_id"):
            prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
            t["property_address"] = prop.get("address", "") if prop else ""
        else:
            t["property_address"] = ""
    return tenants

@api_router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    t = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
    t["current_property"] = t.get("property_id", "")
    # Get documents
    docs = await db.documents.find({"owner_id": tenant_id}, {"_id": 0}).to_list(50)
    t["documents"] = docs
    # Get payments
    payments = await db.payments.find({"tenant_id": tenant_id}, {"_id": 0}).sort("payment_date", -1).to_list(100)
    t["payments"] = payments
    # Get invoices
    invoices = await db.invoices.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    t["invoices"] = invoices
    # Get contracts
    contracts = await db.contracts.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    t["contracts"] = contracts
    # Room info
    if t.get("room_id"):
        room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
        t["room_info"] = room
    if t.get("property_id"):
        prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
        t["property_info"] = prop
    return t

@api_router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, tenant_update: TenantCreate, user: dict = Depends(get_current_user)):
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    update_dict = tenant_update.model_dump()
    await db.tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    # If room changed, update room occupancy
    if update_dict.get("room_id") and update_dict["room_id"] != existing.get("room_id", ""):
        if existing.get("room_id"):
            await db.rooms.update_one({"id": existing["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
        await db.rooms.update_one({"id": update_dict["room_id"]}, {"$set": {"status": "occupied", "tenant_id": tenant_id}})
    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    updated["remaining_balance"] = updated.get("total_due", 0) - updated.get("total_paid", 0)
    updated["current_property"] = updated.get("property_id", "")
    return updated

@api_router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # Free the room
    if tenant.get("room_id"):
        await db.rooms.update_one({"id": tenant["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
    await db.tenants.delete_one({"id": tenant_id})
    return {"message": "Tenant deleted"}

# ============ Landlord Routes ============
@api_router.post("/landlords")
async def create_landlord(landlord: LandlordCreate, user: dict = Depends(get_current_user)):
    d = landlord.model_dump()
    d["id"] = str(uuid.uuid4())
    d["properties_count"] = 0
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.landlords.insert_one(d)
    return {**{k: v for k, v in d.items() if k != "_id"}, "properties_count": 0}

@api_router.get("/landlords")
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

@api_router.get("/landlords/{landlord_id}")
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

@api_router.put("/landlords/{landlord_id}")
async def update_landlord(landlord_id: str, landlord_update: LandlordCreate, user: dict = Depends(get_current_user)):
    existing = await db.landlords.find_one({"id": landlord_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Landlord not found")
    await db.landlords.update_one({"id": landlord_id}, {"$set": landlord_update.model_dump()})
    updated = await db.landlords.find_one({"id": landlord_id}, {"_id": 0})
    updated["properties_count"] = await db.properties.count_documents({"landlord_id": landlord_id})
    return updated

@api_router.delete("/landlords/{landlord_id}")
async def delete_landlord(landlord_id: str, user: dict = Depends(get_current_user)):
    result = await db.landlords.delete_one({"id": landlord_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Landlord not found")
    return {"message": "Landlord deleted"}

# ============ Property Routes ============
@api_router.post("/properties")
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

@api_router.get("/properties")
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

@api_router.get("/properties/{property_id}")
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
    # Get tenants in this property
    tenants = await db.tenants.find({"property_id": property_id}, {"_id": 0}).to_list(100)
    for t in tenants:
        t["remaining_balance"] = t.get("total_due", 0) - t.get("total_paid", 0)
    p["tenants"] = tenants
    return p

@api_router.put("/properties/{property_id}")
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

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str, user: dict = Depends(get_current_user)):
    result = await db.properties.delete_one({"id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    await db.rooms.delete_many({"property_id": property_id})
    return {"message": "Property deleted"}

# ============ Room Routes ============
@api_router.post("/rooms")
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

@api_router.get("/rooms")
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

@api_router.get("/rooms/{room_id}")
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

@api_router.put("/rooms/{room_id}")
async def update_room(room_id: str, room_update: RoomCreate, user: dict = Depends(get_current_user)):
    existing = await db.rooms.find_one({"id": room_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Room not found")
    await db.rooms.update_one({"id": room_id}, {"$set": room_update.model_dump()})
    updated = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    return updated

@api_router.delete("/rooms/{room_id}")
async def delete_room(room_id: str, user: dict = Depends(get_current_user)):
    result = await db.rooms.delete_one({"id": room_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted"}

@api_router.post("/rooms/{room_id}/assign")
async def assign_tenant_to_room(room_id: str, tenant_id: str = Form(...), user: dict = Depends(get_current_user)):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # Free previous room if any
    if tenant.get("room_id"):
        await db.rooms.update_one({"id": tenant["room_id"]}, {"$set": {"status": "available", "tenant_id": ""}})
    # Assign
    await db.rooms.update_one({"id": room_id}, {"$set": {"status": "occupied", "tenant_id": tenant_id}})
    await db.tenants.update_one({"id": tenant_id}, {"$set": {"room_id": room_id, "property_id": room["property_id"]}})
    return {"message": "Tenant assigned to room"}

@api_router.post("/rooms/{room_id}/unassign")
async def unassign_tenant_from_room(room_id: str, user: dict = Depends(get_current_user)):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.get("tenant_id"):
        await db.tenants.update_one({"id": room["tenant_id"]}, {"$set": {"room_id": "", "property_id": ""}})
    await db.rooms.update_one({"id": room_id}, {"$set": {"status": "available", "tenant_id": ""}})
    return {"message": "Tenant unassigned"}

@api_router.post("/rooms/{room_id}/images")
async def upload_room_image(room_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{room_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / "rooms" / filename
    async with aiofiles.open(str(filepath), "wb") as f:
        content = await file.read()
        await f.write(content)
    url = f"/uploads/rooms/{filename}"
    await db.rooms.update_one({"id": room_id}, {"$push": {"images": url}})
    return {"url": url}

# ============ Contract Routes ============
@api_router.post("/contracts")
async def create_contract(contract: ContractCreate, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": contract.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prop = await db.properties.find_one({"id": contract.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    d = contract.model_dump()
    d["id"] = str(uuid.uuid4())
    d["contract_number"] = f"CNT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    d["tenant_name"] = tenant["full_name"]
    d["property_address"] = prop["address"]
    d["status"] = "active"
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.contracts.insert_one(d)
    await db.tenants.update_one({"id": contract.tenant_id}, {"$set": {"property_id": contract.property_id}})
    if contract.room_id:
        await db.rooms.update_one({"id": contract.room_id}, {"$set": {"status": "occupied", "tenant_id": contract.tenant_id}})
        await db.tenants.update_one({"id": contract.tenant_id}, {"$set": {"room_id": contract.room_id}})
    d.pop("_id", None)
    return d

@api_router.get("/contracts")
async def get_contracts(user: dict = Depends(get_current_user)):
    return await db.contracts.find({}, {"_id": 0}).to_list(1000)

@api_router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, user: dict = Depends(get_current_user)):
    c = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    return c

@api_router.put("/contracts/{contract_id}/status")
async def update_contract_status(contract_id: str, status: str, user: dict = Depends(get_current_user)):
    if status not in ["active", "expired", "cancelled", "renewed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.contracts.update_one({"id": contract_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"message": "Status updated"}

@api_router.get("/contracts/{contract_id}/pdf")
async def generate_contract_pdf(contract_id: str, user: dict = Depends(get_current_user)):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#9F1239'), spaceAfter=20, alignment=1)
    elems.append(Paragraph("CONTRATTO DI LOCAZIONE", title_s))
    elems.append(Paragraph("Consulenze immobiliari - Via Vigonovese 114", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=1)))
    elems.append(Spacer(1, 0.4*inch))
    data = [
        ["N. Contratto:", contract['contract_number']],
        ["Inquilino:", contract['tenant_name']],
        ["Immobile:", contract['property_address']],
        ["Data Inizio:", contract['start_date']],
        ["Data Fine:", contract['end_date']],
        ["Affitto Mensile:", f"\u20ac{contract['rent_amount']:.2f}"],
        ["Deposito:", f"\u20ac{contract['deposit_amount']:.2f}"],
        ["Stato:", contract['status'].upper()],
    ]
    t = Table(data, colWidths=[4*cm, 12*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FDF2F8')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB'))
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.3*inch))
    elems.append(Paragraph("<b>Termini e Condizioni:</b>", styles['Heading3']))
    elems.append(Paragraph(contract.get('terms', ''), styles['BodyText']))
    doc.build(elems)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=contratto_{contract['contract_number']}.pdf"})

# ============ Invoice Routes ============
@api_router.post("/invoices")
async def create_invoice(invoice: InvoiceCreate, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": invoice.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prop = await db.properties.find_one({"id": invoice.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    d = invoice.model_dump()
    d["id"] = str(uuid.uuid4())
    d["invoice_number"] = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    d["tenant_name"] = tenant["full_name"]
    d["property_address"] = prop["address"]
    d["issue_date"] = datetime.now(timezone.utc).isoformat()
    d["payment_status"] = "unpaid"
    d["paid_amount"] = 0.0
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.insert_one(d)
    # Update tenant total_due
    await db.tenants.update_one({"id": invoice.tenant_id}, {"$inc": {"total_due": invoice.amount}})
    d.pop("_id", None)
    return d

@api_router.get("/invoices")
async def get_invoices(user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    for inv in invoices:
        inv["paid_amount"] = inv.get("paid_amount", 0)
    return invoices

@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payments = await db.payments.find({"invoice_id": invoice_id}, {"_id": 0}).to_list(100)
    inv["payments"] = payments
    inv["paid_amount"] = inv.get("paid_amount", 0)
    return inv

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    from invoice_generator import generate_luxury_invoice_pdf
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice_data = {
        'invoice_number': invoice['invoice_number'].replace('INV-', ''),
        'date': invoice['issue_date'][:10].replace('-', '/'),
        'time': datetime.now(timezone.utc).strftime('%H:%M'),
        'recipient_name': invoice['tenant_name'],
        'amount': invoice['amount'],
        'description': invoice['description'] or f"Affitto di {invoice['invoice_type']}",
        'currency': '\u20ac'
    }
    pdf_buffer = generate_luxury_invoice_pdf(invoice_data)
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=ricevuta_{invoice['invoice_number']}.pdf"})

# ============ Payment Routes (Enhanced) ============
@api_router.post("/payments")
async def create_payment(payment: PaymentCreate, user: dict = Depends(get_current_user)):
    d = payment.model_dump()
    d["id"] = str(uuid.uuid4())
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    d["created_by"] = user.get("email", "")
    await db.payments.insert_one(d)

    # Update tenant's total_paid
    await db.tenants.update_one({"id": payment.tenant_id}, {"$inc": {"total_paid": payment.amount}})

    # If linked to invoice, update invoice paid_amount
    if payment.invoice_id:
        invoice = await db.invoices.find_one({"id": payment.invoice_id})
        if invoice:
            new_paid = invoice.get("paid_amount", 0) + payment.amount
            status = "paid" if new_paid >= invoice["amount"] else "partial"
            await db.invoices.update_one({"id": payment.invoice_id}, {"$set": {"paid_amount": new_paid, "payment_status": status}})

    d.pop("_id", None)
    return d

@api_router.get("/payments")
async def get_payments(tenant_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"tenant_id": tenant_id} if tenant_id else {}
    payments = await db.payments.find(query, {"_id": 0}).sort("payment_date", -1).to_list(1000)
    for p in payments:
        if p.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": p["tenant_id"]}, {"_id": 0})
            p["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            p["tenant_name"] = ""
    return payments

@api_router.get("/payments/tenant/{tenant_id}")
async def get_tenant_payments(tenant_id: str, user: dict = Depends(get_current_user)):
    payments = await db.payments.find({"tenant_id": tenant_id}, {"_id": 0}).sort("payment_date", -1).to_list(100)
    return payments

# ============ Document Upload Routes ============
@api_router.post("/documents/upload")
async def upload_document(
    owner_id: str = Form(...),
    owner_type: str = Form(...),  # tenant / landlord
    doc_type: str = Form(...),    # passport / id_card / contract / other
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"{owner_type}_{owner_id}_{doc_type}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / "documents" / filename
    async with aiofiles.open(str(filepath), "wb") as f:
        content = await file.read()
        await f.write(content)
    url = f"/uploads/documents/{filename}"
    doc_record = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "owner_type": owner_type,
        "doc_type": doc_type,
        "filename": file.filename,
        "url": url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user.get("email", ""),
    }
    await db.documents.insert_one(doc_record)
    doc_record.pop("_id", None)
    return doc_record

@api_router.get("/documents/{owner_id}")
async def get_documents(owner_id: str, user: dict = Depends(get_current_user)):
    return await db.documents.find({"owner_id": owner_id}, {"_id": 0}).to_list(100)

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    filepath = UPLOAD_DIR / doc["url"].lstrip("/uploads/")
    if filepath.exists():
        filepath.unlink()
    await db.documents.delete_one({"id": doc_id})
    return {"message": "Document deleted"}

# ============ Dashboard Routes ============
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_tenants = await db.tenants.count_documents({})
    total_landlords = await db.landlords.count_documents({})
    total_properties = await db.properties.count_documents({})
    active_contracts = await db.contracts.count_documents({"status": "active"})
    unpaid_invoices = await db.invoices.count_documents({"payment_status": {"$in": ["unpaid", "partial"]}})

    # Room stats
    total_rooms = await db.rooms.count_documents({})
    occupied_rooms = await db.rooms.count_documents({"status": "occupied"})

    # Financial
    contracts_list = await db.contracts.find({"status": "active"}, {"_id": 0, "rent_amount": 1}).to_list(1000)
    total_monthly_income = sum(c.get("rent_amount", 0) for c in contracts_list)
    tenants_list = await db.tenants.find({}, {"_id": 0, "deposit_amount": 1, "total_paid": 1, "total_due": 1}).to_list(1000)
    total_deposits = sum(t.get("deposit_amount", 0) for t in tenants_list)
    total_collected = sum(t.get("total_paid", 0) for t in tenants_list)
    total_outstanding = sum(max(0, t.get("total_due", 0) - t.get("total_paid", 0)) for t in tenants_list)

    # Recent payments
    recent_payments = await db.payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    for p in recent_payments:
        if p.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": p["tenant_id"]}, {"_id": 0})
            p["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            p["tenant_name"] = ""

    # Overdue invoices
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

# ============ Reports ============
@api_router.get("/reports/generate")
async def generate_report(
    report_type: str = Query("monthly"),
    period: str = Query(""),
    user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    if report_type == "weekly":
        start = (now - timedelta(days=7)).isoformat()
    elif report_type == "monthly":
        start = (now - timedelta(days=30)).isoformat()
    elif report_type == "yearly":
        start = (now - timedelta(days=365)).isoformat()
    else:
        start = (now - timedelta(days=30)).isoformat()

    payments = await db.payments.find({"created_at": {"$gte": start}}, {"_id": 0}).to_list(5000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(1000)

    total_received = sum(p.get("amount", 0) for p in payments)
    unpaid = [i for i in invoices if i.get("payment_status") in ["unpaid", "partial"]]
    partial = [i for i in invoices if i.get("payment_status") == "partial"]
    today = now.strftime("%Y-%m-%d")
    overdue = [i for i in unpaid if i.get("due_date", "9999") < today]
    occupied = sum(1 for r in rooms if r.get("status") == "occupied")

    tenant_balances = []
    for t in tenants:
        bal = t.get("total_due", 0) - t.get("total_paid", 0)
        if bal > 0:
            tenant_balances.append({"name": t["full_name"], "balance": bal})

    return {
        "report_type": report_type,
        "generated_at": now.isoformat(),
        "period_start": start,
        "summary": {
            "total_payments_received": total_received,
            "payment_count": len(payments),
            "unpaid_invoices": len(unpaid),
            "partial_payments": len(partial),
            "overdue_invoices": len(overdue),
            "total_overdue_amount": sum(i.get("amount", 0) - i.get("paid_amount", 0) for i in overdue),
            "total_rooms": len(rooms),
            "occupied_rooms": occupied,
            "vacant_rooms": len(rooms) - occupied,
            "occupancy_rate": round(occupied / max(len(rooms), 1) * 100, 1),
        },
        "tenant_balances": sorted(tenant_balances, key=lambda x: -x["balance"]),
        "recent_payments": payments[:20],
        "overdue_details": overdue[:20],
    }

@api_router.get("/reports/pdf")
async def generate_report_pdf(
    report_type: str = Query("monthly"),
    user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    if report_type == "weekly":
        start = now - timedelta(days=7)
        title = "Report Settimanale"
    elif report_type == "yearly":
        start = now - timedelta(days=365)
        title = "Report Annuale"
    else:
        start = now - timedelta(days=30)
        title = "Report Mensile"

    payments = await db.payments.find({"created_at": {"$gte": start.isoformat()}}, {"_id": 0}).to_list(5000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(1000)

    total_received = sum(p.get("amount", 0) for p in payments)
    unpaid = [i for i in invoices if i.get("payment_status") in ["unpaid", "partial"]]
    occupied = sum(1 for r in rooms if r.get("status") == "occupied")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    elems = []

    # Header
    h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#9F1239'), alignment=1)
    elems.append(Paragraph(f"Consulenze immobiliari - {title}", h1))
    elems.append(Paragraph(f"Periodo: {start.strftime('%d/%m/%Y')} - {now.strftime('%d/%m/%Y')}", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, textColor=colors.grey)))
    elems.append(Spacer(1, 0.4*inch))

    # Summary table
    summary_data = [
        ["Metrica", "Valore"],
        ["Pagamenti Ricevuti", f"\u20ac{total_received:,.2f}"],
        ["N. Pagamenti", str(len(payments))],
        ["Fatture Non Pagate", str(len(unpaid))],
        ["Stanze Totali", str(len(rooms))],
        ["Stanze Occupate", str(occupied)],
        ["Stanze Libere", str(len(rooms) - occupied)],
        ["Tasso Occupazione", f"{round(occupied / max(len(rooms), 1) * 100, 1)}%"],
    ]
    t = Table(summary_data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9F1239')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF7ED')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.3*inch))

    # Tenant balances
    elems.append(Paragraph("<b>Saldi Inquilini</b>", styles['Heading3']))
    bal_data = [["Inquilino", "Dovuto", "Pagato", "Saldo"]]
    for ten in tenants:
        due = ten.get("total_due", 0)
        paid = ten.get("total_paid", 0)
        bal = due - paid
        if due > 0 or paid > 0:
            bal_data.append([ten["full_name"], f"\u20ac{due:,.2f}", f"\u20ac{paid:,.2f}", f"\u20ac{bal:,.2f}"])
    if len(bal_data) > 1:
        bt = Table(bal_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 4*cm])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9F1239')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(bt)
    else:
        elems.append(Paragraph("Nessun dato disponibile", styles['Normal']))

    doc.build(elems)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=report_{report_type}_{now.strftime('%Y%m%d')}.pdf"})

# ============ Notifications ============
@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = []
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")

    # Overdue invoices
    overdue = await db.invoices.find({"payment_status": {"$in": ["unpaid", "partial"]}, "due_date": {"$lt": today_str}}, {"_id": 0}).to_list(100)
    for inv in overdue:
        notifications.append({
            "type": "overdue_payment",
            "severity": "high",
            "title": f"Pagamento scaduto: {inv['tenant_name']}",
            "message": f"Fattura {inv['invoice_number']} di \u20ac{inv['amount']:.2f} scaduta il {inv['due_date']}",
            "tenant_id": inv["tenant_id"],
            "date": inv["due_date"],
        })

    # Upcoming payments (next 7 days)
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming = await db.invoices.find({"payment_status": {"$in": ["unpaid", "partial"]}, "due_date": {"$gte": today_str, "$lte": next_week}}, {"_id": 0}).to_list(100)
    for inv in upcoming:
        notifications.append({
            "type": "upcoming_payment",
            "severity": "medium",
            "title": f"Pagamento in scadenza: {inv['tenant_name']}",
            "message": f"Fattura {inv['invoice_number']} di \u20ac{inv['amount']:.2f} scade il {inv['due_date']}",
            "tenant_id": inv["tenant_id"],
            "date": inv["due_date"],
        })

    # Expiring contracts (next 30 days)
    next_month = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    expiring = await db.contracts.find({"status": "active", "end_date": {"$lte": next_month}}, {"_id": 0}).to_list(100)
    for c in expiring:
        notifications.append({
            "type": "contract_expiry",
            "severity": "medium",
            "title": f"Contratto in scadenza: {c['tenant_name']}",
            "message": f"Contratto {c['contract_number']} scade il {c['end_date']}",
            "tenant_id": c["tenant_id"],
            "date": c["end_date"],
        })

    # Expiring passports (next 90 days)
    next_90 = (today + timedelta(days=90)).strftime("%Y-%m-%d")
    tenants = await db.tenants.find({"passport_expiry_date": {"$lte": next_90}}, {"_id": 0}).to_list(100)
    for t in tenants:
        notifications.append({
            "type": "passport_expiry",
            "severity": "low",
            "title": f"Passaporto in scadenza: {t['full_name']}",
            "message": f"Passaporto scade il {t['passport_expiry_date']}",
            "tenant_id": t["id"],
            "date": t["passport_expiry_date"],
        })

    # Birthdays today/this week
    for t in await db.tenants.find({}, {"_id": 0}).to_list(1000):
        dob = t.get("date_of_birth", "")
        if dob:
            try:
                dob_md = dob[5:]  # MM-DD
                today_md = today.strftime("%m-%d")
                if dob_md == today_md:
                    notifications.append({
                        "type": "birthday",
                        "severity": "info",
                        "title": f"Compleanno oggi: {t['full_name']}",
                        "message": f"Auguri a {t['full_name']}!",
                        "tenant_id": t["id"],
                        "date": today_str,
                    })
            except Exception:
                pass

    notifications.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2, "info": 3}.get(x["severity"], 4))
    return notifications

# ============ Email placeholder ============
@api_router.post("/send-email")
async def send_email_endpoint(user: dict = Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Servizio email non ancora configurato.")

# ============ Include Routers ============
app.include_router(auth_router)
app.include_router(api_router)

frontend_url = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
origins = [o.strip() for o in frontend_url.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
