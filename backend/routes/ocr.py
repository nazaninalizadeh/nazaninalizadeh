"""OCR Routes - Passport/ID scanning with OpenAI Vision."""

from fastapi import APIRouter, UploadFile, File, Depends
from auth import get_current_user
from services.ocr_service import scan_document, get_scan_status

router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post("/scan")
async def ocr_scan_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a passport/ID image for OCR scanning."""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type and file.content_type not in allowed_types:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Formato file non supportato. Usa JPEG, PNG o WebP.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="File troppo grande. Massimo 10MB.")

    result = await scan_document(content, file.filename or "document")
    return result


@router.get("/scan/{scan_id}")
async def ocr_get_status(scan_id: str, user: dict = Depends(get_current_user)):
    """Get the status and result of an OCR scan."""
    result = await get_scan_status(scan_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Scansione non trovata")
    return result
