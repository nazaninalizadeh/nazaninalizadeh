"""
Monthly Payment Status - editable per-tenant per-month status with contract-based auto-late.
Collection: monthly_status { tenant_id, month, year, status, amount, payment_method, payment_date, manual_override, notes, updated_by, updated_at }
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Payment Calendar"])

MONTH_NAMES = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


class MonthStatusUpdate(BaseModel):
    status: str  # paid, not_paid, late
    amount: Optional[float] = 0
    payment_method: Optional[str] = ""
    payment_date: Optional[str] = ""
    notes: Optional[str] = ""


async def _compute_month_status(tenant_id: str, month: int, year: int, due_day: int, created_at: str = "") -> dict:
    """Compute status for a single month, checking manual overrides first, then payments, then contract-based auto-late."""
    now = datetime.now(timezone.utc)

    # 1. Check for manual override
    override = await db.monthly_status.find_one(
        {"tenant_id": tenant_id, "month": month, "year": year},
        {"_id": 0}
    )
    if override and override.get("status"):
        return {
            "month": month,
            "month_name": MONTH_NAMES[month],
            "year": year,
            "status": override.get("status", "not_paid"),
            "amount": override.get("amount", 0),
            "payment_method": override.get("payment_method", ""),
            "payment_date": override.get("payment_date", ""),
            "notes": override.get("notes", ""),
            "manual_override": True,
            "updated_at": override.get("updated_at", ""),
            "receipt_url": override.get("receipt_url", ""),
            "receipt_filename": override.get("receipt_filename", ""),
            "contract_id": override.get("contract_id", ""),
        }

    # 2. Check actual payment records
    month_start = f"{year}-{month:02d}-01"
    month_end = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"

    payments = await db.payments.find(
        {"tenant_id": tenant_id, "payment_date": {"$gte": month_start, "$lt": month_end}},
        {"_id": 0}
    ).to_list(10)

    # Receipt info (if uploaded but no manual status set)
    extra_receipt = {
        "receipt_url": (override or {}).get("receipt_url", ""),
        "receipt_filename": (override or {}).get("receipt_filename", ""),
        "contract_id": (override or {}).get("contract_id", ""),
    }

    if payments:
        total = sum(p.get("amount", 0) for p in payments)
        methods = list(set(p.get("payment_method", "") for p in payments if p.get("payment_method")))
        method_map = {"contanti": "Contanti", "cash": "Contanti", "bonifico": "Bonifico", "bank_transfer": "Bonifico"}
        raw = methods[0] if len(methods) == 1 else ", ".join(methods)
        return {
            "month": month, "month_name": MONTH_NAMES[month], "year": year,
            "status": "paid", "amount": total,
            "payment_method": method_map.get(raw, raw.capitalize() if raw else ""),
            "payment_date": payments[0].get("payment_date", ""),
            "notes": "", "manual_override": False, "updated_at": "",
            **extra_receipt,
        }

    # 3. Check if month is before tenant creation → "none"
    if created_at:
        try:
            cd = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if year < cd.year or (year == cd.year and month < cd.month):
                return {
                    "month": month, "month_name": MONTH_NAMES[month], "year": year,
                    "status": "none", "amount": 0, "payment_method": "", "payment_date": "",
                    "notes": "", "manual_override": False, "updated_at": "",
                    **extra_receipt,
                }
        except Exception:
            pass

    # 4. Auto-determine: In Ritardo if 1 day past due_day
    if year < now.year or (year == now.year and month < now.month):
        status = "late"
    elif year == now.year and month == now.month:
        today_day = int(now.strftime("%d"))
        status = "late" if today_day > due_day else "not_paid"
    else:
        status = "not_paid"

    return {
        "month": month, "month_name": MONTH_NAMES[month], "year": year,
        "status": status, "amount": 0, "payment_method": "", "payment_date": "",
        "notes": "", "manual_override": False, "updated_at": "",
        **extra_receipt,
    }


@router.get("/payment-calendar/{tenant_id}")
async def get_payment_calendar(tenant_id: str, year: int = 0, user: dict = Depends(get_current_user)):
    """Get 12-month payment calendar for a tenant."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    now = datetime.now(timezone.utc)
    if year == 0:
        year = now.year

    # Get due_day: prefer from contract, fallback to tenant setting
    due_day = tenant.get("payment_due_day", 5)
    contract = await db.contracts.find_one({"tenant_id": tenant_id, "status": "active"}, {"_id": 0})
    if contract and contract.get("payment_due_day"):
        due_day = contract["payment_due_day"]

    created_at = tenant.get("created_at", "")
    calendar = []

    for month in range(1, 13):
        m = await _compute_month_status(tenant_id, month, year, due_day, created_at)
        calendar.append(m)

    return {"tenant_id": tenant_id, "year": year, "due_day": due_day, "calendar": calendar}


@router.put("/payment-calendar/{tenant_id}/{year}/{month}")
async def update_month_status(
    tenant_id: str, year: int, month: int,
    update: MonthStatusUpdate,
    user: dict = Depends(get_current_user),
):
    """Manually set the payment status for a specific month."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mese non valido")
    if update.status not in ("paid", "not_paid", "late"):
        raise HTTPException(status_code=400, detail="Stato non valido. Usa: paid, not_paid, late")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    now = datetime.now(timezone.utc).isoformat()

    # Upsert the manual override
    await db.monthly_status.update_one(
        {"tenant_id": tenant_id, "month": month, "year": year},
        {"$set": {
            "tenant_id": tenant_id,
            "month": month,
            "year": year,
            "status": update.status,
            "amount": update.amount or 0,
            "payment_method": update.payment_method or "",
            "payment_date": update.payment_date or "",
            "notes": update.notes or "",
            "manual_override": True,
            "updated_by": user.get("email", ""),
            "updated_at": now,
        }},
        upsert=True,
    )

    return {
        "message": f"Stato {MONTH_NAMES[month]} {year} aggiornato a {update.status}",
        "tenant_id": tenant_id,
        "month": month,
        "year": year,
        "status": update.status,
    }


@router.delete("/payment-calendar/{tenant_id}/{year}/{month}")
async def reset_month_status(
    tenant_id: str, year: int, month: int,
    user: dict = Depends(get_current_user),
):
    """Remove manual override and revert to auto-calculated status."""
    await db.monthly_status.delete_one(
        {"tenant_id": tenant_id, "month": month, "year": year}
    )
    return {"message": "Override rimosso, stato calcolato automaticamente"}


# ---- Receipt upload per month ---------------------------------------------
import os
import shutil
from fastapi import UploadFile, File

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "receipts")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


@router.post("/payment-calendar/{tenant_id}/{year}/{month}/receipt")
async def upload_month_receipt(
    tenant_id: str, year: int, month: int,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a payment receipt (PDF/image) for a specific month/year."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mese non valido")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Formato non supportato. Usa PDF/PNG/JPG/WEBP.")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    # Find linked active contract (if any)
    contract = await db.contracts.find_one(
        {"tenant_id": tenant_id, "status": "active"}, {"_id": 0, "id": 1}
    )
    contract_id = contract.get("id") if contract else ""

    # Persist file with unique name
    filename = f"{tenant_id}_{year}_{month:02d}_{uuid.uuid4().hex[:8]}{ext}"
    abs_path = os.path.join(UPLOAD_DIR, filename)
    with open(abs_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    receipt_url = f"/uploads/receipts/{filename}"

    now = datetime.now(timezone.utc).isoformat()
    await db.monthly_status.update_one(
        {"tenant_id": tenant_id, "month": month, "year": year},
        {"$set": {
            "tenant_id": tenant_id, "month": month, "year": year,
            "contract_id": contract_id,
            "receipt_url": receipt_url,
            "receipt_filename": file.filename,
            "receipt_uploaded_at": now,
            "receipt_uploaded_by": user.get("email", ""),
            "updated_at": now,
        }},
        upsert=True,
    )
    return {"message": "Ricevuta caricata", "receipt_url": receipt_url, "contract_id": contract_id}


@router.delete("/payment-calendar/{tenant_id}/{year}/{month}/receipt")
async def delete_month_receipt(
    tenant_id: str, year: int, month: int,
    user: dict = Depends(get_current_user),
):
    """Delete an uploaded receipt for a month."""
    rec = await db.monthly_status.find_one(
        {"tenant_id": tenant_id, "month": month, "year": year}, {"_id": 0}
    )
    if rec and rec.get("receipt_url"):
        # remove physical file (best effort)
        rel = rec["receipt_url"].lstrip("/")
        abs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), rel)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except OSError:
            pass
    await db.monthly_status.update_one(
        {"tenant_id": tenant_id, "month": month, "year": year},
        {"$unset": {"receipt_url": "", "receipt_filename": "", "receipt_uploaded_at": "", "receipt_uploaded_by": ""}},
    )
    return {"message": "Ricevuta eliminata"}


@router.get("/late-tenants")
async def get_late_tenants(user: dict = Depends(get_current_user)):
    """Get all tenants with late payment status for dashboard/notifications."""
    now = datetime.now(timezone.utc)
    current_month = now.month
    current_year = now.year
    today_day = int(now.strftime("%d"))

    tenants = await db.tenants.find({"room_id": {"$ne": ""}}, {"_id": 0}).to_list(1000)
    late_list = []

    for t in tenants:
        due_day = t.get("payment_due_day", 5)
        m = await _compute_month_status(t["id"], current_month, current_year, due_day, t.get("created_at", ""))

        if m["status"] == "late":
            # Get property/room info
            prop_addr = ""
            room_num = ""
            if t.get("property_id"):
                prop = await db.properties.find_one({"id": t["property_id"]}, {"_id": 0})
                prop_addr = prop.get("address", "") if prop else ""
            if t.get("room_id"):
                room = await db.rooms.find_one({"id": t["room_id"]}, {"_id": 0})
                room_num = room.get("room_number", "") if room else ""

            late_list.append({
                "tenant_id": t["id"],
                "tenant_name": t.get("full_name", ""),
                "property_address": prop_addr,
                "room_number": room_num,
                "month": current_month,
                "month_name": MONTH_NAMES[current_month],
                "year": current_year,
                "due_day": due_day,
                "status": "late",
            })

    return late_list
