"""Payment Routes - Simplified: no deposit math, just record payments."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
import uuid
import aiofiles
from datetime import datetime, timezone
from pathlib import Path

from database import db
from auth import get_current_user
from models.schemas import PaymentCreate

router = APIRouter(prefix="/api", tags=["Payments"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
ALLOWED_RECEIPT_EXTS = {"jpg", "jpeg", "png", "webp", "pdf"}


@router.post("/payments")
async def create_payment(payment: PaymentCreate, user: dict = Depends(get_current_user)):
    # Validate tenant exists
    tenant = await db.tenants.find_one({"id": payment.tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    d = payment.model_dump()
    d["id"] = str(uuid.uuid4())
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    d["created_by"] = user.get("email", "")
    await db.payments.insert_one(d)

    # If linked to invoice, update invoice paid_amount (invoice logic is separate from deposit)
    if payment.invoice_id:
        invoice = await db.invoices.find_one({"id": payment.invoice_id})
        if invoice:
            new_paid = invoice.get("paid_amount", 0) + payment.amount
            status = "paid" if new_paid >= invoice["amount"] else "partial"
            await db.invoices.update_one({"id": payment.invoice_id}, {"$set": {"paid_amount": new_paid, "payment_status": status}})

    d.pop("_id", None)
    return d


@router.get("/payments")
async def get_payments(tenant_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"tenant_id": tenant_id} if tenant_id else {}
    payments = await db.payments.find(query, {"_id": 0}).sort("payment_date", -1).to_list(1000)
    for p in payments:
        if p.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": p["tenant_id"]}, {"_id": 0})
            if tenant:
                p["tenant_name"] = tenant.get("full_name", "")
                p["property_id"] = tenant.get("property_id", "")
                p["room_id"] = tenant.get("room_id", "")
                # Add property address and room number
                if tenant.get("property_id"):
                    prop = await db.properties.find_one({"id": tenant["property_id"]}, {"_id": 0})
                    p["property_address"] = prop.get("address", "") if prop else ""
                else:
                    p["property_address"] = ""
                if tenant.get("room_id"):
                    room = await db.rooms.find_one({"id": tenant["room_id"]}, {"_id": 0})
                    p["room_number"] = room.get("room_number", "") if room else ""
                else:
                    p["room_number"] = ""
            else:
                p["tenant_name"] = ""
                p["property_id"] = ""
                p["room_id"] = ""
                p["property_address"] = ""
                p["room_number"] = ""
        else:
            p["tenant_name"] = ""
            p["property_id"] = ""
            p["room_id"] = ""
            p["property_address"] = ""
            p["room_number"] = ""
    return payments


@router.get("/payments/tenant/{tenant_id}")
async def get_tenant_payments(tenant_id: str, user: dict = Depends(get_current_user)):
    payments = await db.payments.find({"tenant_id": tenant_id}, {"_id": 0}).sort("payment_date", -1).to_list(100)
    return payments


@router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str, user: dict = Depends(get_current_user)):
    """Delete a single payment record. Reverses the linked invoice's paid_amount if any."""
    p = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Pagamento non trovato")
    if p.get("invoice_id"):
        inv = await db.invoices.find_one({"id": p["invoice_id"]})
        if inv:
            new_paid = max(0, inv.get("paid_amount", 0) - p.get("amount", 0))
            new_status = "paid" if new_paid >= inv.get("amount", 0) and new_paid > 0 else ("partial" if new_paid > 0 else "pending")
            await db.invoices.update_one({"id": p["invoice_id"]}, {"$set": {"paid_amount": new_paid, "payment_status": new_status}})
    await db.payments.delete_one({"id": payment_id})
    return {"message": "Pagamento eliminato"}


@router.post("/payments/{payment_id}/receipt")
async def upload_payment_receipt(
    payment_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Attach a card receipt (image or PDF) to an existing payment."""
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="File non valido")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_RECEIPT_EXTS:
        raise HTTPException(status_code=400, detail="Solo JPG/PNG/WEBP/PDF")
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Massimo 10MB")
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento non trovato")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "receipts").mkdir(exist_ok=True)
    fname = f"receipt_{payment_id}_{uuid.uuid4().hex[:8]}.{ext}"
    fpath = UPLOAD_DIR / "receipts" / fname
    async with aiofiles.open(str(fpath), "wb") as f:
        await f.write(raw)
    url = f"/api/uploads/receipts/{fname}"
    await db.payments.update_one({"id": payment_id}, {"$set": {"receipt_url": url}})
    return {"url": url}


@router.get("/payments/overview")
async def get_payment_overview(user: dict = Depends(get_current_user)):
    """Get current month payment overview grouped by property → room → tenant."""
    now = datetime.now(timezone.utc)
    month_start = now.strftime("%Y-%m-01")
    if now.month == 12:
        month_end = f"{now.year + 1}-01-01"
    else:
        month_end = f"{now.year}-{now.month + 1:02d}-01"

    properties = await db.properties.find({}, {"_id": 0}).to_list(500)
    result = []

    for prop in properties:
        rooms = await db.rooms.find({"property_id": prop["id"]}, {"_id": 0}).to_list(200)
        room_list = []
        for room in rooms:
            room_data = {
                "id": room["id"],
                "room_number": room.get("room_number", ""),
                "room_type": room.get("room_type", ""),
                "status": room.get("status", "available"),
                "tenant_id": "",
                "tenant_name": "",
                "payment_status": "empty",
                "payment_amount": 0,
                "payment_method": "",
            }
            if room.get("tenant_id"):
                tenant = await db.tenants.find_one({"id": room["tenant_id"]}, {"_id": 0})
                if tenant:
                    room_data["tenant_id"] = tenant["id"]
                    room_data["tenant_name"] = tenant.get("full_name", "")
                    # Check current month payments
                    month_payments = await db.payments.find(
                        {"tenant_id": tenant["id"], "payment_date": {"$gte": month_start, "$lt": month_end}}
                    , {"_id": 0}).to_list(10)
                    if month_payments:
                        total = sum(p.get("amount", 0) for p in month_payments)
                        methods = list(set(p.get("payment_method", "") for p in month_payments))
                        raw = methods[0] if len(methods) == 1 else ", ".join(methods)
                        method_map = {"contanti": "Contanti", "cash": "Contanti", "bonifico": "Bonifico", "bank_transfer": "Bonifico", "carta": "Carta"}
                        room_data["payment_status"] = "paid"
                        room_data["payment_amount"] = total
                        room_data["payment_method"] = method_map.get(raw, raw.capitalize() if raw else "")
                    else:
                        room_data["payment_status"] = "not_paid"
            room_list.append(room_data)
        room_list.sort(key=lambda r: r["room_number"])

        paid_count = sum(1 for r in room_list if r["payment_status"] == "paid")
        not_paid_count = sum(1 for r in room_list if r["payment_status"] == "not_paid")

        result.append({
            "id": prop["id"],
            "property_code": prop.get("property_code", ""),
            "address": prop.get("address", ""),
            "landlord_name": prop.get("landlord_name", ""),
            "total_rooms": len(room_list),
            "paid_count": paid_count,
            "not_paid_count": not_paid_count,
            "rooms": room_list,
        })

    return result
