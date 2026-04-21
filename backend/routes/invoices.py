"""Invoice Routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import InvoiceCreate

router = APIRouter(prefix="/api", tags=["Invoices"])


@router.post("/invoices")
async def create_invoice(invoice: InvoiceCreate, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": invoice.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prop = await db.properties.find_one({"id": invoice.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    d = invoice.model_dump()
    d["id"] = str(uuid.uuid4())
    d["invoice_number"] = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    d["tenant_name"] = tenant["full_name"]
    d["property_address"] = prop["address"]
    d["issue_date"] = datetime.now(timezone.utc).isoformat()
    d["payment_status"] = "unpaid"
    d["paid_amount"] = 0.0
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.insert_one(d)
    await db.tenants.update_one({"id": invoice.tenant_id}, {"$inc": {"total_due": invoice.amount}})
    d.pop("_id", None)
    return d


@router.get("/invoices")
async def get_invoices(user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    for inv in invoices:
        inv["paid_amount"] = inv.get("paid_amount", 0)
    return invoices


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payments = await db.payments.find({"invoice_id": invoice_id}, {"_id": 0}).to_list(100)
    inv["payments"] = payments
    inv["paid_amount"] = inv.get("paid_amount", 0)
    return inv


@router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    from invoice_generator import generate_luxury_invoice_pdf
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice_data = {
        'invoice_number': invoice['invoice_number'].replace('INV-', ''),
        'date': invoice['issue_date'][:10].replace('-', '/'),
        'time': datetime.now(timezone.utc).strftime('%H:%M'),
        'recipient_name': invoice['tenant_name'],
        'amount': invoice['amount'],
        'description': invoice['description'] or f"Affitto di {invoice['invoice_type']}",
        'currency': '\u20ac'
    }
    pdf_buffer = generate_luxury_invoice_pdf(invoice_data)
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=ricevuta_{invoice['invoice_number']}.pdf"})
