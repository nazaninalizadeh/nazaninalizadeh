"""Registration and Document Bundle Routes."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
import io
import zipfile
import aiofiles

from auth import get_current_user
from database import db

router = APIRouter(prefix="/api", tags=["Registration"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "documents"


@router.post("/registration/upload")
async def upload_registration_doc(
    owner_id: str = Form(...),
    doc_type: str = Form("registration"),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a registration document."""
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "pdf"
    filename = f"reg_{owner_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / filename
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(filepath), "wb") as f:
        content = await file.read()
        await f.write(content)
    url = f"/api/uploads/documents/{filename}"
    doc_record = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "owner_type": "tenant",
        "doc_type": doc_type,
        "filename": file.filename,
        "url": url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user.get("email", ""),
    }
    await db.documents.insert_one(doc_record)
    doc_record.pop("_id", None)
    return doc_record


@router.post("/contracts/upload")
async def upload_signed_contract(
    tenant_id: str = Form(...),
    property_id: str = Form(""),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a signed contract file."""
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "pdf"
    filename = f"contract_{tenant_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / filename
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(filepath), "wb") as f:
        content = await file.read()
        await f.write(content)
    url = f"/api/uploads/documents/{filename}"
    doc_record = {
        "id": str(uuid.uuid4()),
        "owner_id": tenant_id,
        "owner_type": "tenant",
        "doc_type": "contract",
        "filename": file.filename,
        "url": url,
        "property_id": property_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user.get("email", ""),
    }
    await db.documents.insert_one(doc_record)
    doc_record.pop("_id", None)
    return doc_record


@router.post("/owner-documents/upload")
async def upload_owner_document(
    owner_id: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload an owner/landlord document."""
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "pdf"
    filename = f"owner_{owner_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / filename
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(filepath), "wb") as f:
        content = await file.read()
        await f.write(content)
    url = f"/api/uploads/documents/{filename}"
    doc_record = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "owner_type": "landlord",
        "doc_type": "owner_document",
        "filename": file.filename,
        "url": url,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user.get("email", ""),
    }
    await db.documents.insert_one(doc_record)
    doc_record.pop("_id", None)
    return doc_record


@router.get("/documents/bundle/{tenant_id}")
async def generate_document_bundle(tenant_id: str, user: dict = Depends(get_current_user)):
    """Generate a ZIP bundle for a tenant. Always includes the auto-generated
    Hospitality PDF + a Registration summary, plus any uploaded tenant + landlord
    documents and the active contract PDF when present.
    """
    from services.hospitality_pdf import generate_hospitality_pdf
    from datetime import datetime as _dt

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    # Resolve linked records
    landlord = None
    prop = None
    if tenant.get("property_id"):
        prop = await db.properties.find_one({"id": tenant["property_id"]}, {"_id": 0})
        if prop and prop.get("landlord_id"):
            landlord = await db.landlords.find_one({"id": prop["landlord_id"]}, {"_id": 0})
    contract = await db.contracts.find_one({"tenant_id": tenant_id, "status": "active"}, {"_id": 0})

    docs = await db.documents.find({"owner_id": tenant_id}, {"_id": 0}).to_list(100)
    landlord_docs = []
    if landlord:
        landlord_docs = await db.documents.find({"owner_id": landlord["id"]}, {"_id": 0}).to_list(20)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1) Auto-generated Hospitality PDF (always)
        try:
            ll_name = (landlord or {}).get("full_name", "")
            ll_split = ll_name.split(" ", 1) if ll_name else ["", ""]
            t_name = tenant.get("full_name", "")
            t_split = t_name.split(" ", 1) if t_name else ["", ""]
            addr = (prop or {}).get("address", "")
            import re as _re
            m = _re.search(r"(?:,\s*|\s)(\d+[A-Z]?)\s*$", addr.strip()) if addr else None
            auto_number = m.group(1) if m else ""
            addr_via = addr[:m.start()].rstrip(", ").strip() if m else (addr or "")
            hosp_data = {
                "host_surname": ll_split[0], "host_name": ll_split[1] if len(ll_split) > 1 else "",
                "host_dob": (landlord or {}).get("date_of_birth", ""),
                "host_birth_place": (landlord or {}).get("place_of_birth", ""),
                "host_province": (landlord or {}).get("province_of_birth", ""),
                "host_residence": (landlord or {}).get("residence", ""),
                "host_signature_url": (landlord or {}).get("signature_url", ""),
                "guest_surname": t_split[0], "guest_name": t_split[1] if len(t_split) > 1 else "",
                "guest_dob": tenant.get("date_of_birth", ""),
                "guest_birth_place": tenant.get("place_of_birth", ""),
                "guest_birth_nation": tenant.get("country_of_birth", "") or tenant.get("nationality", ""),
                "guest_citizenship": tenant.get("nationality", ""),
                "guest_residence": tenant.get("address", ""),
                "doc_type": "PASSAPORTO",
                "passport_number": tenant.get("passport_number", ""),
                "doc_issue_date": tenant.get("passport_issue_date", ""),
                "doc_authority": tenant.get("issuing_authority", ""),
                "check_in_date": (contract or {}).get("start_date", ""),
                "check_out_date": (contract or {}).get("end_date", ""),
                "hosting_type": "alloggio",
                "property_comune": (prop or {}).get("city", "") or ((landlord or {}).get("residence", "").split(",")[0] if (landlord or {}).get("residence") else ""),
                "property_provincia": (prop or {}).get("province", "PD"),
                "property_address": addr_via, "property_number": auto_number,
                "property_interno": "", "property_piano": "",
            }
            hosp_pdf = generate_hospitality_pdf(hosp_data)
            zf.writestr("05_Ospitalita/comunicazione_ospitalita.pdf", hosp_pdf.getvalue())
        except Exception:
            pass

        # 2) Registration summary (text)
        reg_lines = [
            "MODULO DI REGISTRAZIONE",
            "=" * 50, "",
            f"Inquilino: {tenant.get('full_name','')}",
            f"Passaporto: {tenant.get('passport_number','')}",
            f"Nazionalità: {tenant.get('nationality','')}",
            f"Data di nascita: {tenant.get('date_of_birth','')}",
            f"Luogo di nascita: {tenant.get('place_of_birth','')}, {tenant.get('country_of_birth','')}",
            f"Email: {tenant.get('email','')}", f"Telefono: {tenant.get('phone','')}",
            "", "IMMOBILE", "-" * 30,
            f"Indirizzo: {(prop or {}).get('address','—')}",
            f"Codice: {(prop or {}).get('property_code','—')}",
            "", "PROPRIETARIO", "-" * 30,
            f"Nome: {(landlord or {}).get('full_name','—')}",
            f"Email: {(landlord or {}).get('email','—')}",
            f"Tel: {(landlord or {}).get('phone','—')}",
            "", "CONTRATTO", "-" * 30,
            f"Numero: {(contract or {}).get('contract_number','—')}",
            f"Inizio: {(contract or {}).get('start_date','—')}",
            f"Fine: {(contract or {}).get('end_date','—')}",
            "", f"Generato il: {_dt.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}",
        ]
        zf.writestr("02_Registrazione/registrazione.txt", "\n".join(reg_lines).encode("utf-8"))

        # 3) Uploaded tenant + landlord documents
        for doc in docs + landlord_docs:
            file_url = doc.get("url", "")
            if not file_url:
                continue
            try:
                rel = file_url.lstrip("/").replace("api/", "", 1)
                file_path = Path(__file__).parent.parent / rel
                if file_path.exists():
                    doc_type = doc.get("doc_type", "other")
                    original_name = doc.get("filename", file_path.name)
                    folder = {
                        "passport": "01_Documenti_Inquilino",
                        "id_card": "01_Documenti_Inquilino",
                        "codice_fiscale": "01_Documenti_Inquilino",
                        "registration": "02_Registrazione",
                        "contract": "03_Contratto",
                        "owner_document": "04_Proprietario",
                        "hospitality": "05_Ospitalita",
                    }.get(doc_type, "06_Altri")
                    zf.write(str(file_path), f"{folder}/{original_name}")
            except Exception:
                continue

    buf.seek(0)
    safe_name = tenant.get("full_name", "documenti").replace(" ", "_")
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=documenti_{safe_name}.zip"},
    )
