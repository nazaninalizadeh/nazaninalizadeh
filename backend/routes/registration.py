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
    """Generate a ZIP bundle of all documents for a tenant (Hospitality, Registration, Contract, Owner docs)."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    docs = await db.documents.find({"owner_id": tenant_id}, {"_id": 0}).to_list(100)

    # Also get landlord docs if tenant has property
    landlord_docs = []
    if tenant.get("property_id"):
        prop = await db.properties.find_one({"id": tenant["property_id"]}, {"_id": 0})
        if prop and prop.get("landlord_id"):
            landlord_docs = await db.documents.find({"owner_id": prop["landlord_id"]}, {"_id": 0}).to_list(20)

    all_docs = docs + landlord_docs
    if not all_docs:
        raise HTTPException(status_code=404, detail="Nessun documento trovato per questo inquilino")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in all_docs:
            file_url = doc.get("url", "")
            if not file_url:
                continue
            file_path = Path(__file__).parent.parent / file_url.lstrip("/")
            if file_path.exists():
                doc_type = doc.get("doc_type", "other")
                original_name = doc.get("filename", "document")
                # Organize in folders
                folder = {
                    "passport": "01_Documenti",
                    "id_card": "01_Documenti",
                    "codice_fiscale": "01_Documenti",
                    "registration": "02_Registrazione",
                    "contract": "03_Contratto",
                    "owner_document": "04_Proprietario",
                    "hospitality": "05_Ospitalita",
                }.get(doc_type, "06_Altri")
                zf.write(str(file_path), f"{folder}/{original_name}")

    buf.seek(0)
    safe_name = tenant.get("full_name", "documenti").replace(" ", "_")
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=documenti_{safe_name}.zip"},
    )
