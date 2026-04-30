"""Invoice Routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models.schemas import InvoiceCreate
from services.invoice_pdf import generate_fattura_pdf, generate_preavviso_pdf

router = APIRouter(prefix="/api", tags=["Invoices"])


@router.post("/invoices")
async def create_invoice(invoice: InvoiceCreate, user: dict = Depends(get_current_user)):
    d = invoice.model_dump()
    # Normalise recipient info
    tenant_name = ""
    property_address = ""
    if invoice.tenant_id:
        tenant = await db.tenants.find_one({"id": invoice.tenant_id}, {"_id": 0})
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        tenant_name = tenant.get("full_name", "")
    if invoice.property_id:
        prop = await db.properties.find_one({"id": invoice.property_id}, {"_id": 0})
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
        property_address = prop.get("address", "")

    # For preavviso without tenant, use the overridden recipient name
    if not tenant_name:
        tenant_name = invoice.recipient_name or ""

    d["id"] = str(uuid.uuid4())
    d["invoice_number"] = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    d["tenant_name"] = tenant_name
    d["property_address"] = property_address
    d["issue_date"] = datetime.now(timezone.utc).isoformat()
    d["payment_status"] = "unpaid"
    d["paid_amount"] = 0.0
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.insert_one(d)
    if invoice.tenant_id:
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


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    inv = await db.invoices.find_one({"id": invoice_id})
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.invoices.delete_one({"id": invoice_id})
    if inv.get("tenant_id"):
        await db.tenants.update_one({"id": inv["tenant_id"]}, {"$inc": {"total_due": -float(inv.get("amount") or 0)}})
    return {"message": "Invoice deleted"}


def _build_fattura_data(invoice: dict) -> dict:
    """Build the data dict expected by generate_fattura_pdf()."""
    amount = float(invoice.get("amount") or 0)
    vat_rate = float(invoice.get("vat_rate") or 22)
    # Imponibile = if user supplied explicit "imponibile" use it,
    # otherwise treat the stored amount as already-inclusive and back-compute
    if invoice.get("imponibile"):
        imponibile = float(invoice["imponibile"])
    else:
        # If the UI put the sum of components in amount, and vat is on rent/agency
        # we fall back to treating amount as the base (imponibile)
        imponibile = amount

    return {
        "invoice_number": invoice.get("invoice_number", "").replace("INV-", ""),
        "invoice_date": invoice.get("issue_date", "")[:10] or invoice.get("due_date", ""),
        "recipient_name": invoice.get("recipient_name") or invoice.get("tenant_name", ""),
        "recipient_address": invoice.get("recipient_address") or invoice.get("property_address", ""),
        "recipient_city": invoice.get("recipient_city", ""),
        "recipient_piva": invoice.get("recipient_cf_piva", ""),
        "recipient_cf": invoice.get("recipient_cf_piva", ""),
        "line_description": invoice.get("description") or invoice.get("body_text") or "",
        "line_amount": imponibile,
        "vat_rate": vat_rate,
        "due_date": invoice.get("due_date", ""),
    }


def _build_preavviso_data(invoice: dict) -> dict:
    """Build the data dict expected by generate_preavviso_pdf()."""
    return {
        "causale_date": invoice.get("issue_date", "")[:10] or invoice.get("due_date", ""),
        "recipient_name": invoice.get("recipient_name") or invoice.get("tenant_name", ""),
        "recipient_address": invoice.get("recipient_address") or invoice.get("property_address", ""),
        "recipient_cf_piva": invoice.get("recipient_cf_piva", ""),
        "body_text": invoice.get("body_text") or invoice.get("description", ""),
        "imponibile": float(invoice.get("imponibile") or invoice.get("amount") or 0),
        "vat_rate": float(invoice.get("vat_rate") or 22),
        "rimborso_label": invoice.get("rimborso_label", ""),
        "rimborso_amount": float(invoice.get("rimborso_amount") or 0),
        "rimborso_note": invoice.get("rimborso_note", ""),
        "rimborso_tax_note": invoice.get("rimborso_tax_note", ""),
    }


@router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    doc_type = (invoice.get("document_type") or "fattura").lower()
    if doc_type == "preavviso":
        buf = generate_preavviso_pdf(_build_preavviso_data(invoice))
        filename = f"preavviso_{invoice['invoice_number']}.pdf"
    else:
        buf = generate_fattura_pdf(_build_fattura_data(invoice))
        filename = f"fattura_{invoice['invoice_number']}.pdf"

    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
