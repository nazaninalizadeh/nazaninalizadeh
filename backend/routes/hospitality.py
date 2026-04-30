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
    signature_type: Optional[str] = "owner"
    guest_doc_authority: Optional[str] = ""


@router.post("/records")
async def create_hospitality_record(record: HospitalityCreate, user: dict = Depends(get_current_user)):
    """Create or UPDATE a hospitality record for a tenant. Idempotent by tenant_id."""
    tenant = await db.tenants.find_one({"id": record.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    prop = await db.properties.find_one({"id": record.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Immobile non trovato")

    d = record.model_dump()
    d["tenant_name"] = tenant.get("full_name", "")
    d["property_address"] = prop.get("address", "")
    d["status"] = "active"
    d["updated_at"] = datetime.now(timezone.utc).isoformat()
    d["updated_by"] = user.get("email", "")

    existing = await db.hospitality_records.find_one({"tenant_id": record.tenant_id}, {"_id": 0})
    if existing:
        d["id"] = existing.get("id") or str(uuid.uuid4())
        await db.hospitality_records.update_one({"tenant_id": record.tenant_id}, {"$set": d})
    else:
        d["id"] = str(uuid.uuid4())
        d["created_at"] = d["updated_at"]
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

    # Try to get dates from active contract; default to 1-year duration if no contract
    if not check_in_date:
        contract = await db.contracts.find_one({"tenant_id": tenant_id, "status": "active"}, {"_id": 0})
        if contract:
            check_in_date = contract.get("start_date", "")
            if not check_out_date:
                check_out_date = contract.get("end_date", "")
    if check_in_date and not check_out_date:
        # Default duration: 1 year from check-in
        try:
            from datetime import datetime as _dt, timedelta as _td
            base = _dt.strptime(check_in_date[:10], "%Y-%m-%d")
            check_out_date = (base.replace(year=base.year + 1)).strftime("%Y-%m-%d")
        except Exception:
            pass

    # Also check for an existing hospitality record
    hosp_record = await db.hospitality_records.find_one({"tenant_id": tenant_id}, {"_id": 0})

    # Split landlord into Surname/Name. Prefer explicit fields; otherwise
    # treat the LAST word of full_name as surname (Italian/Cognome convention)
    # so legacy data stored as "Larisa Pasincovschi" maps correctly to
    # Cognome=Pasincovschi, Nome=Larisa.
    if landlord_data.get("surname") or landlord_data.get("name"):
        ll_surname = landlord_data.get("surname", "") or ""
        ll_first = landlord_data.get("name", "") or ""
    else:
        ll_name = landlord_data.get("full_name", "") or ""
        parts = ll_name.strip().split()
        if len(parts) >= 2:
            ll_surname = parts[-1]
            ll_first = " ".join(parts[:-1])
        else:
            ll_surname = ll_name
            ll_first = ""

    # Same logic for tenant
    if tenant.get("surname") or tenant.get("name"):
        t_surname = tenant.get("surname", "") or ""
        t_first = tenant.get("name", "") or ""
    else:
        t_name = tenant.get("full_name", "") or ""
        parts = t_name.strip().split()
        if len(parts) >= 2:
            t_surname = parts[-1]
            t_first = " ".join(parts[:-1])
        else:
            t_surname = t_name
            t_first = ""

    # Extract address parts
    addr = property_data.get("address", "")
    # Best-effort defaults for property fields when no hospitality_record exists.
    # property_comune: prefer explicit field, fall back to city, then landlord_residence city.
    auto_comune = (
        property_data.get("city")
        or property_data.get("comune")
        or (landlord_data.get("residence", "").split(",")[0].strip() if landlord_data.get("residence") else "")
    )
    auto_provincia = (property_data.get("province") or property_data.get("provincia") or "")
    # Try to extract civic number from a string like "Via X, 12" or "Via X 12"
    auto_number = ""
    if addr:
        import re
        m = re.search(r"(?:,\s*|\s)(\d+[A-Z]?)\s*$", addr.strip())
        if m:
            auto_number = m.group(1)
            addr_via = addr[:m.start()].rstrip(", ").strip()
        else:
            addr_via = addr
    else:
        addr_via = ""

    # Host residence default from landlord
    auto_host_residence = landlord_data.get("residence", "") or landlord_data.get("address", "")

    pdf_data = {
        # Host (landlord/declarant)
        "host_surname": hosp_record.get("host_surname", ll_surname) if hosp_record else ll_surname,
        "host_name": hosp_record.get("host_name", ll_first) if hosp_record else ll_first,
        "host_dob": hosp_record.get("host_dob", landlord_data.get("date_of_birth", "")) if hosp_record else landlord_data.get("date_of_birth", ""),
        "host_birth_place": hosp_record.get("host_birth_place", landlord_data.get("place_of_birth", "")) if hosp_record else landlord_data.get("place_of_birth", ""),
        "host_province": hosp_record.get("host_province", landlord_data.get("province_of_birth", "")) if hosp_record else landlord_data.get("province_of_birth", ""),
        "host_residence": hosp_record.get("host_residence", auto_host_residence) if hosp_record else auto_host_residence,
        "host_signature_url": landlord_data.get("signature_url", ""),
        # Guest (tenant)
        "guest_surname": t_surname,
        "guest_name": t_first,
        "guest_dob": tenant.get("date_of_birth", ""),
        "guest_birth_place": tenant.get("place_of_birth", ""),
        "guest_birth_nation": tenant.get("country_of_birth", "") or tenant.get("nationality", ""),
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
        "property_comune": hosp_record.get("property_comune", auto_comune) if hosp_record else auto_comune,
        "property_provincia": hosp_record.get("property_provincia", auto_provincia) if hosp_record else auto_provincia,
        "property_address": addr_via or addr,
        "property_number": hosp_record.get("property_number", auto_number) if hosp_record else auto_number,
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
