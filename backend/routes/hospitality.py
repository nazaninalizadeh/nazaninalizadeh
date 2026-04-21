"""Hospitality (Ospitalità) PDF Routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from auth import get_current_user
from database import db
from services.hospitality_pdf import generate_hospitality_pdf

router = APIRouter(prefix="/api/hospitality", tags=["Hospitality"])


@router.get("/pdf/{tenant_id}")
async def download_hospitality_pdf(
    tenant_id: str,
    check_in_date: str = Query(""),
    check_out_date: str = Query(""),
    user: dict = Depends(get_current_user),
):
    """Generate and download a hospitality (Ospitalità) PDF for a tenant."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    # Gather property and room data
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

    # If no check_in, use contract start date
    if not check_in_date:
        contract = await db.contracts.find_one(
            {"tenant_id": tenant_id, "status": "active"}, {"_id": 0}
        )
        if contract:
            check_in_date = contract.get("start_date", "")
            if not check_out_date:
                check_out_date = contract.get("end_date", "")

    pdf_data = {
        "tenant_name": tenant.get("full_name", ""),
        "passport_number": tenant.get("passport_number", ""),
        "nationality": tenant.get("nationality", ""),
        "date_of_birth": tenant.get("date_of_birth", ""),
        "gender": tenant.get("gender", ""),
        "place_of_birth": tenant.get("place_of_birth", ""),
        "passport_issue_date": tenant.get("passport_issue_date", ""),
        "passport_expiry_date": tenant.get("passport_expiry_date", ""),
        "codice_fiscale": tenant.get("codice_fiscale", ""),
        "property_address": property_data.get("address", ""),
        "property_code": property_data.get("property_code", ""),
        "room_number": room_data.get("room_number", ""),
        "room_type": room_data.get("room_type", ""),
        "landlord_name": landlord_data.get("full_name", ""),
        "landlord_codice_fiscale": landlord_data.get("codice_fiscale", ""),
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
    }

    pdf_buf = generate_hospitality_pdf(pdf_data)

    safe_name = tenant.get("full_name", "document").replace(" ", "_")
    return Response(
        content=pdf_buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ospitalita_{safe_name}.pdf"},
    )
