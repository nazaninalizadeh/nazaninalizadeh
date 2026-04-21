"""Payment Routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import PaymentCreate

router = APIRouter(prefix="/api", tags=["Payments"])


@router.post("/payments")
async def create_payment(payment: PaymentCreate, user: dict = Depends(get_current_user)):
    d = payment.model_dump()
    d["id"] = str(uuid.uuid4())
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    d["created_by"] = user.get("email", "")
    await db.payments.insert_one(d)
    await db.tenants.update_one({"id": payment.tenant_id}, {"$inc": {"total_paid": payment.amount}})
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
            p["tenant_name"] = tenant.get("full_name", "") if tenant else ""
        else:
            p["tenant_name"] = ""
    return payments


@router.get("/payments/tenant/{tenant_id}")
async def get_tenant_payments(tenant_id: str, user: dict = Depends(get_current_user)):
    payments = await db.payments.find({"tenant_id": tenant_id}, {"_id": 0}).sort("payment_date", -1).to_list(100)
    return payments
