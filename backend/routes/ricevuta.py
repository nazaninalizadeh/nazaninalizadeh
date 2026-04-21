"""Ricevuta (Receipt) PDF Routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from auth import get_current_user
from database import db
from services.ricevuta_pdf import generate_ricevuta_pdf

router = APIRouter(prefix="/api/ricevuta", tags=["Ricevuta"])


class RicevutaRequest(BaseModel):
    tenant_id: str
    amount: float
    receipt_number: str
    description_lines: Optional[List[str]] = []
    note: Optional[str] = ""


@router.post("/generate")
async def generate_ricevuta(req: RicevutaRequest, user: dict = Depends(get_current_user)):
    """Generate a Ricevuta PDF from tenant and payment data."""
    tenant = await db.tenants.find_one({"id": req.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    now = datetime.now(timezone.utc)
    pdf_data = {
        "receipt_number": req.receipt_number,
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M"),
        "amount": req.amount,
        "recipient_name": tenant.get("full_name", ""),
        "description_lines": req.description_lines if req.description_lines else [],
        "note": req.note or "",
    }

    pdf_buf = generate_ricevuta_pdf(pdf_data)
    safe_name = tenant.get("full_name", "ricevuta").replace(" ", "_")
    return Response(
        content=pdf_buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ricevuta_{safe_name}_{req.receipt_number}.pdf"},
    )


@router.get("/from-payment/{payment_id}")
async def generate_ricevuta_from_payment(payment_id: str, user: dict = Depends(get_current_user)):
    """Generate a Ricevuta PDF from an existing payment record."""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento non trovato")

    tenant = await db.tenants.find_one({"id": payment.get("tenant_id", "")}, {"_id": 0})
    tenant_name = tenant.get("full_name", "") if tenant else ""

    now = datetime.now(timezone.utc)
    # Build description from payment
    method_map = {"contanti": "Contanti", "bonifico": "Bonifico", "carta": "Carta"}
    method = method_map.get(payment.get("payment_method", ""), payment.get("payment_method", ""))
    pay_date = payment.get("payment_date", "")

    desc_lines = [f"Affitto di mese ({payment['amount']:.2f} euro) - {method}"]
    if payment.get("notes"):
        desc_lines.append(payment["notes"])

    pdf_data = {
        "receipt_number": payment["id"][:8].upper(),
        "date": pay_date if pay_date else now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M"),
        "amount": payment.get("amount", 0),
        "recipient_name": tenant_name,
        "description_lines": desc_lines,
        "note": "",
    }

    pdf_buf = generate_ricevuta_pdf(pdf_data)
    safe_name = tenant_name.replace(" ", "_") if tenant_name else "ricevuta"
    return Response(
        content=pdf_buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ricevuta_{safe_name}.pdf"},
    )
