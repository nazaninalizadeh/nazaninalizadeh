"""Hospitality (Ospitalità) PDF and CRUD Routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone

from auth import get_current_user
from database import db
from services.hospitality_pdf import generate_hospitality_pdf

router = APIRouter(prefix="/api/hospitality", tags=["Hospitality"])


class HospitalityCreate(BaseModel):
    tenant_id: str
    property_id: str
    room_id: Optional[str] = ""
    check_in_date: str
    check_out_date: Optional[str] = ""
    hosting_type: Optional[str] = "alloggio"
    host_surname: Optional[str] = ""
    host_name: Optional[str] = ""
    host_dob: Optional[str] = ""
    host_birth_place: Optional[str] = ""
    host_province: Optional[str] = ""
    host_residence: Optional[str] = ""
    property_comune: Optional[str] = ""
    property_provincia: Optional[str] = ""
    property_number: Optional[str] = ""
    property_interno: Optional[str] = ""
    property_piano: Optional[str] = ""
    notes: Optional[str] = ""


@router.post("/records")
async def create_hospitality_record(record: HospitalityCreate, user: dict = Depends(get_current_user)):
    """Create a new hospitality record."""
    tenant = await db.tenants.find_one({"id": record.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    prop = await db.properties.find_one({"id": record.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Immobile non trovato")

    d = record.model_dump()
    d["id"] = str(uuid.uuid4())
    d["tenant_name"] = tenant.get("full_name", "")
    d["property_address"] = prop.get("address", "")
    d["status"] = "active"
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    d["created_by"] = user.get("email", "")
    await db.hospitality_records.insert_one(d)
    d.pop("_id", None)
    return d


@router.get("/records")
async def get_hospitality_records(user: dict = Depends(get_current_user)):
    """List all hospitality records."""
    records = await db.hospitality_records.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    for r in records:
        tenant = await db.tenants.find_one({"id": r.get("tenant_id", "")}, {"_id": 0})
        if tenant:
            r["tenant_name"] = tenant.get("full_name", "")
            r["tenant_nationality"] = tenant.get("nationality", "")
            r["tenant_passport"] = tenant.get("passport_number", "")
        prop = await db.properties.find_one({"id": r.get("property_id", "")}, {"_id": 0})
        if prop:
            r["property_address"] = prop.get("address", "")
    return records


@router.get("/pdf/{tenant_id}")
async def download_hospitality_pdf(
    tenant_id: str,
    check_in_date: str = Query(""),
    check_out_date: str = Query(""),
    user: dict = Depends(get_current_user),
):
    """Generate and download a hospitality PDF for a tenant."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    # Gather property, room, landlord data
    property_data = {}
    room_data = {}
    landlord_data = {}

    if tenant.get("property_id"):
        prop = await db.properties.find_one({"id": tenant["property_id"]}, {"_id": 0})
        if prop:
            property_data = prop
            if prop.get("landlord_id"):
                ll = await db.landlords.find_one({"id": prop["landlord_id"]}, {"_id": 0})
                if ll:
                    landlord_data = ll

    if tenant.get("room_id"):
        room = await db.rooms.find_one({"id": tenant["room_id"]}, {"_id": 0})
        if room:
            room_data = room

    # Try to get dates from active contract
    if not check_in_date:
        contract = await db.contracts.find_one({"tenant_id": tenant_id, "status": "active"}, {"_id": 0})
        if contract:
            check_in_date = contract.get("start_date", "")
            if not check_out_date:
                check_out_date = contract.get("end_date", "")

    # Also check for an existing hospitality record
    hosp_record = await db.hospitality_records.find_one({"tenant_id": tenant_id}, {"_id": 0})

    # Split landlord name for the form
    ll_name = landlord_data.get("full_name", "")
    ll_parts = ll_name.rsplit(" ", 1) if ll_name else ["", ""]
    ll_surname = ll_parts[0] if len(ll_parts) > 1 else ll_name
    ll_first = ll_parts[1] if len(ll_parts) > 1 else ""

    # Split tenant name
    t_name = tenant.get("full_name", "")
    t_parts = t_name.rsplit(" ", 1) if t_name else ["", ""]
    t_surname = t_parts[0] if len(t_parts) > 1 else t_name
    t_first = t_parts[1] if len(t_parts) > 1 else ""

    # Extract address parts
    addr = property_data.get("address", "")

    pdf_data = {
        # Host (landlord/declarant)
        "host_surname": hosp_record.get("host_surname", ll_surname) if hosp_record else ll_surname,
        "host_name": hosp_record.get("host_name", ll_first) if hosp_record else ll_first,
        "host_dob": hosp_record.get("host_dob", "") if hosp_record else "",
        "host_birth_place": hosp_record.get("host_birth_place", "") if hosp_record else "",
        "host_province": hosp_record.get("host_province", "") if hosp_record else "",
        "host_residence": hosp_record.get("host_residence", "") if hosp_record else "",
        # Guest (tenant)
        "guest_surname": t_surname,
        "guest_name": t_first,
        "guest_dob": tenant.get("date_of_birth", ""),
        "guest_birth_place": tenant.get("place_of_birth", ""),
        "guest_birth_nation": tenant.get("nationality", ""),
        "guest_citizenship": tenant.get("nationality", ""),
        "guest_residence": tenant.get("address", ""),
        "doc_type": "PASSAPORTO",
        "passport_number": tenant.get("passport_number", ""),
        "doc_issue_date": tenant.get("passport_issue_date", ""),
        "doc_authority": "",
        # Duration
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "hosting_type": hosp_record.get("hosting_type", "alloggio") if hosp_record else "alloggio",
        # Property
        "property_comune": hosp_record.get("property_comune", "") if hosp_record else "",
        "property_provincia": hosp_record.get("property_provincia", "") if hosp_record else "",
        "property_address": addr,
        "property_number": hosp_record.get("property_number", "") if hosp_record else "",
        "property_interno": hosp_record.get("property_interno", "") if hosp_record else "",
        "property_piano": hosp_record.get("property_piano", "") if hosp_record else "",
    }

    pdf_buf = generate_hospitality_pdf(pdf_data)
    safe_name = tenant.get("full_name", "document").replace(" ", "_")
    return Response(
        content=pdf_buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ospitalita_{safe_name}.pdf"},
    )
