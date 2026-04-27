"""OCR Routes - Passport/ID scanning with OpenAI Vision. Saves original document."""

from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from typing import Optional
from pathlib import Path
import uuid
import aiofiles

from auth import get_current_user
from services.ocr_service import scan_document, get_scan_status
from database import db
from datetime import datetime, timezone

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "documents"


@router.post("/scan")
async def ocr_scan_document(
    file: UploadFile = File(...),
    owner_id: Optional[str] = Form(""),
    user: dict = Depends(get_current_user),
):
    """Upload a passport/ID image for OCR scanning. Saves original file."""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Formato file non supportato. Usa JPEG, PNG o WebP.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Massimo 10MB.")

    # Save original file
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    saved_filename = f"ocr_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / saved_filename
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(filepath), "wb") as f:
        await f.write(content)
    saved_url = f"/api/uploads/documents/{saved_filename}"

    # Run OCR
    result = await scan_document(content, file.filename or "document")

    # Detect document type from OCR result
    doc_type = "other"
    if result.get("extracted_data"):
        dt = result["extracted_data"].get("document_type", "")
        if dt == "passport":
            doc_type = "passport"
        elif dt == "id_card":
            doc_type = "id_card"
        elif "codice" in str(result["extracted_data"].get("codice_fiscale", "")).lower():
            doc_type = "codice_fiscale"

    # Save document record if owner_id provided
    if owner_id:
        doc_record = {
            "id": str(uuid.uuid4()),
            "owner_id": owner_id,
            "owner_type": "tenant",
            "doc_type": doc_type,
            "filename": file.filename,
            "url": saved_url,
            "ocr_scan_id": result.get("id", ""),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": user.get("email", ""),
        }
        await db.documents.insert_one(doc_record)

        # Try face extraction for profile photo
        try:
            from PIL import Image as PILImage
            import io as pio
            img = PILImage.open(pio.BytesIO(content))
            # Simple crop of top portion as face region (basic approach)
            w, h = img.size
            if w > 100 and h > 100:
                face_crop = img.crop((int(w*0.3), int(h*0.05), int(w*0.7), int(h*0.45)))
                face_filename = f"face_{owner_id}_{uuid.uuid4().hex[:6]}.jpg"
                face_path = UPLOAD_DIR / face_filename
                face_crop.save(str(face_path), "JPEG", quality=80)
                face_url = f"/api/uploads/documents/{face_filename}"
                await db.tenants.update_one({"id": owner_id}, {"$set": {"profile_photo": face_url}})
        except Exception:
            pass

    result["saved_file_url"] = saved_url
    result["detected_doc_type"] = doc_type
    return result


@router.get("/scan/{scan_id}")
async def ocr_get_status(scan_id: str, user: dict = Depends(get_current_user)):
    result = await get_scan_status(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scansione non trovata")
    return result
