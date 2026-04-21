"""Data Exchange Routes - Excel/CSV Import & Export."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response
from auth import get_current_user
from services.excel_service import (
    generate_tenant_template,
    generate_payment_template,
    export_tenants,
    export_payments,
    export_occupancy,
    import_tenants_from_file,
    import_payments_from_file,
)

router = APIRouter(prefix="/api/data", tags=["Data Exchange"])


# ============ Templates ============

@router.get("/templates/tenants")
async def download_tenant_template(user: dict = Depends(get_current_user)):
    buf = generate_tenant_template()
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_inquilini.xlsx"},
    )


@router.get("/templates/payments")
async def download_payment_template(user: dict = Depends(get_current_user)):
    buf = generate_payment_template()
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_pagamenti.xlsx"},
    )


# ============ Exports ============

@router.get("/export/tenants")
async def export_tenants_excel(user: dict = Depends(get_current_user)):
    buf = await export_tenants()
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inquilini_export.xlsx"},
    )


@router.get("/export/payments")
async def export_payments_excel(user: dict = Depends(get_current_user)):
    buf = await export_payments()
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=pagamenti_export.xlsx"},
    )


@router.get("/export/occupancy")
async def export_occupancy_excel(user: dict = Depends(get_current_user)):
    buf = await export_occupancy()
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=occupazione_export.xlsx"},
    )


# ============ Imports ============

@router.post("/import/tenants")
async def import_tenants(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome file mancante")

    allowed_ext = (".xlsx", ".xls", ".csv")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa Excel (.xlsx) o CSV (.csv)")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Massimo 10MB.")

    success, errors = await import_tenants_from_file(content, file.filename, user.get("email", ""))
    return {
        "success_count": success,
        "error_count": len(errors),
        "errors": errors[:50],
        "message": f"{success} inquilini importati con successo" + (f", {len(errors)} errori" if errors else ""),
    }


@router.post("/import/payments")
async def import_payments(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome file mancante")

    allowed_ext = (".xlsx", ".xls", ".csv")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa Excel (.xlsx) o CSV (.csv)")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Massimo 10MB.")

    success, errors = await import_payments_from_file(content, file.filename, user.get("email", ""))
    return {
        "success_count": success,
        "error_count": len(errors),
        "errors": errors[:50],
        "message": f"{success} pagamenti importati con successo" + (f", {len(errors)} errori" if errors else ""),
    }
