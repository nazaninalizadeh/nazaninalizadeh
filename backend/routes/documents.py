"""Document Upload Routes."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import uuid
from datetime import datetime, timezone
from pathlib import Path
import aiofiles

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Documents"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"


@router.post("/documents/upload")
async def upload_document(
    owner_id: str = Form(...),
    owner_type: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "pdf"
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


@router.get("/documents/{owner_id}")
async def get_documents(owner_id: str, user: dict = Depends(get_current_user)):
    return await db.documents.find({"owner_id": owner_id}, {"_id": 0}).to_list(100)


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    filepath = UPLOAD_DIR / doc["url"].lstrip("/uploads/")
    if filepath.exists():
        filepath.unlink()
    await db.documents.delete_one({"id": doc_id})
    return {"message": "Document deleted"}
