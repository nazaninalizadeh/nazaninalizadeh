"""Contract Routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from io import BytesIO
import uuid
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch, cm

from database import db
from auth import get_current_user
from models.schemas import ContractCreate

router = APIRouter(prefix="/api", tags=["Contracts"])


@router.post("/contracts")
async def create_contract(contract: ContractCreate, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": contract.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    prop = await db.properties.find_one({"id": contract.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    d = contract.model_dump()
    d["id"] = str(uuid.uuid4())
    d["contract_number"] = f"CNT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    d["tenant_name"] = tenant["full_name"]
    d["property_address"] = prop["address"]
    d["status"] = "active"
    d["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.contracts.insert_one(d)
    await db.tenants.update_one({"id": contract.tenant_id}, {"$set": {"property_id": contract.property_id}})
    if contract.room_id:
        await db.rooms.update_one({"id": contract.room_id}, {"$set": {"status": "occupied", "tenant_id": contract.tenant_id}})
        await db.tenants.update_one({"id": contract.tenant_id}, {"$set": {"room_id": contract.room_id}})
    d.pop("_id", None)
    return d


@router.get("/contracts")
async def get_contracts(user: dict = Depends(get_current_user)):
    return await db.contracts.find({}, {"_id": 0}).to_list(1000)


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, user: dict = Depends(get_current_user)):
    c = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    return c


@router.put("/contracts/{contract_id}/status")
async def update_contract_status(contract_id: str, status: str, user: dict = Depends(get_current_user)):
    if status not in ["active", "expired", "cancelled", "renewed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.contracts.update_one({"id": contract_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"message": "Status updated"}


@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str, user: dict = Depends(get_current_user)):
    """Delete a contract. Does not auto-evict tenant — that's a separate action in /tenants."""
    result = await db.contracts.delete_one({"id": contract_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contratto non trovato")
    return {"message": "Contratto eliminato"}


@router.get("/contracts/{contract_id}/pdf")
async def generate_contract_pdf(contract_id: str, user: dict = Depends(get_current_user)):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#9F1239'), spaceAfter=20, alignment=1)
    elems.append(Paragraph("CONTRATTO DI LOCAZIONE", title_s))
    elems.append(Paragraph("Consulenze immobiliari - Via Vigonovese 114", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=1)))
    elems.append(Spacer(1, 0.4 * inch))
    data = [
        ["N. Contratto:", contract['contract_number']],
        ["Inquilino:", contract['tenant_name']],
        ["Immobile:", contract['property_address']],
        ["Data Inizio:", contract['start_date']],
        ["Data Fine:", contract['end_date']],
        ["Affitto Mensile:", f"\u20ac{contract['rent_amount']:.2f}"],
        ["Deposito:", f"\u20ac{contract['deposit_amount']:.2f}"],
        ["Stato:", contract['status'].upper()],
    ]
    t = Table(data, colWidths=[4 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FDF2F8')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB'))
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.3 * inch))
    elems.append(Paragraph("<b>Termini e Condizioni:</b>", styles['Heading3']))
    elems.append(Paragraph(contract.get('terms', ''), styles['BodyText']))
    doc.build(elems)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=contratto_{contract['contract_number']}.pdf"})
