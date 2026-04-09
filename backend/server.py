from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import asyncio
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import base64

from database import db, client
from auth import auth_router, get_current_user, seed_admins, ALLOWED_ADMINS

app = FastAPI()
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)

# ============ Models ============

class TenantCreate(BaseModel):
    full_name: str
    passport_number: str
    nationality: str
    date_of_birth: str
    passport_issue_date: str
    passport_expiry_date: str
    phone: str
    email: EmailStr
    whatsapp: str
    address: str
    occupation: str
    notes: Optional[str] = ""
    deposit_amount: float = 0.0

class TenantResponse(BaseModel):
    id: str
    full_name: str
    passport_number: str
    nationality: str
    date_of_birth: str
    passport_issue_date: str
    passport_expiry_date: str
    phone: str
    email: str
    whatsapp: str
    address: str
    occupation: str
    notes: str
    deposit_amount: float
    total_paid: float
    remaining_balance: float
    current_property: Optional[str] = None
    created_at: str

class LandlordCreate(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    whatsapp: str
    id_number: str
    bank_details: str
    notes: Optional[str] = ""

class LandlordResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    email: str
    whatsapp: str
    id_number: str
    bank_details: str
    notes: str
    properties_count: int
    created_at: str

class PropertyCreate(BaseModel):
    property_code: str
    address: str
    property_type: str
    number_of_rooms: int
    capacity: int
    landlord_id: str
    rental_amount: float
    deposit_amount: float
    additional_charges: Optional[str] = ""

class PropertyResponse(BaseModel):
    id: str
    property_code: str
    address: str
    property_type: str
    number_of_rooms: int
    capacity: int
    landlord_id: str
    landlord_name: str
    rental_amount: float
    deposit_amount: float
    additional_charges: str
    occupancy_status: str
    current_tenants_count: int
    created_at: str

class ContractCreate(BaseModel):
    tenant_id: str
    property_id: str
    start_date: str
    end_date: str
    rent_amount: float
    deposit_amount: float
    terms: str

class ContractResponse(BaseModel):
    id: str
    contract_number: str
    tenant_id: str
    tenant_name: str
    property_id: str
    property_address: str
    start_date: str
    end_date: str
    rent_amount: float
    deposit_amount: float
    terms: str
    status: str
    created_at: str

class InvoiceCreate(BaseModel):
    tenant_id: str
    property_id: str
    contract_id: str
    invoice_type: str
    amount: float
    due_date: str
    description: str

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    tenant_id: str
    tenant_name: str
    property_id: str
    property_address: str
    contract_id: str
    invoice_type: str
    amount: float
    issue_date: str
    due_date: str
    payment_status: str
    description: str
    created_at: str

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str
    payment_date: str

class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: float
    payment_method: str
    payment_date: str
    created_at: str

# ============ Startup & Admin Seeding ============
@app.on_event("startup")
async def startup_event():
    # Create indexes for data collections
    await db.tenants.create_index("passport_number")
    await db.properties.create_index("property_code")
    await db.contracts.create_index("contract_number")
    await db.invoices.create_index("invoice_number")

    # Seed admins (from auth module)
    await seed_admins()

    # Write credentials file
    from pathlib import Path as P
    P("/app/memory").mkdir(exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write("## Admin 1 (Super Admin)\n")
        f.write(f"- Email: {os.environ.get('ADMIN1_EMAIL')}\n")
        f.write(f"- Password: {os.environ.get('ADMIN1_PASSWORD')}\n")
        f.write("- Role: super_admin\n\n")
        f.write("## Admin 2\n")
        f.write(f"- Email: {os.environ.get('ADMIN2_EMAIL')}\n")
        f.write(f"- Password: {os.environ.get('ADMIN2_PASSWORD')}\n")
        f.write("- Role: admin\n\n")
        f.write("## Auth Flow\n")
        f.write("- Step 1: POST /api/auth/login-step1 (email + password + captcha)\n")
        f.write("- Step 2: POST /api/auth/verify-otp (login_session_id + otp_code)\n")
        f.write("- OTP is logged to backend console (check backend logs)\n")
        f.write("- GET /api/auth/me, POST /api/auth/logout\n")

# ============ Tenant Routes ============
@api_router.post("/tenants", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, user: dict = Depends(get_current_user)):
    tenant_dict = tenant.model_dump()
    tenant_dict["id"] = str(uuid.uuid4())
    tenant_dict["total_paid"] = 0.0
    tenant_dict["remaining_balance"] = 0.0
    tenant_dict["current_property"] = None
    tenant_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    tenant_dict["created_by"] = user["id"]
    
    await db.tenants.insert_one(tenant_dict)
    
    tenant_dict["remaining_balance"] = tenant_dict["deposit_amount"] - tenant_dict["total_paid"]
    return tenant_dict

@api_router.get("/tenants", response_model=List[TenantResponse])
async def get_tenants(user: dict = Depends(get_current_user)):
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    for tenant in tenants:
        tenant["remaining_balance"] = tenant.get("deposit_amount", 0) - tenant.get("total_paid", 0)
    return tenants

@api_router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant["remaining_balance"] = tenant.get("deposit_amount", 0) - tenant.get("total_paid", 0)
    return tenant

@api_router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, tenant_update: TenantCreate, user: dict = Depends(get_current_user)):
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_dict = tenant_update.model_dump()
    await db.tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    
    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    updated["remaining_balance"] = updated.get("deposit_amount", 0) - updated.get("total_paid", 0)
    return updated

@api_router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, user: dict = Depends(get_current_user)):
    result = await db.tenants.delete_one({"id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}

# ============ Landlord Routes ============
@api_router.post("/landlords", response_model=LandlordResponse)
async def create_landlord(landlord: LandlordCreate, user: dict = Depends(get_current_user)):
    landlord_dict = landlord.model_dump()
    landlord_dict["id"] = str(uuid.uuid4())
    landlord_dict["properties_count"] = 0
    landlord_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    landlord_dict["created_by"] = user["id"]
    
    await db.landlords.insert_one(landlord_dict)
    return landlord_dict

@api_router.get("/landlords", response_model=List[LandlordResponse])
async def get_landlords(user: dict = Depends(get_current_user)):
    landlords = await db.landlords.find({}, {"_id": 0}).to_list(1000)
    for landlord in landlords:
        count = await db.properties.count_documents({"landlord_id": landlord["id"]})
        landlord["properties_count"] = count
    return landlords

@api_router.get("/landlords/{landlord_id}", response_model=LandlordResponse)
async def get_landlord(landlord_id: str, user: dict = Depends(get_current_user)):
    landlord = await db.landlords.find_one({"id": landlord_id}, {"_id": 0})
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    count = await db.properties.count_documents({"landlord_id": landlord_id})
    landlord["properties_count"] = count
    return landlord

@api_router.put("/landlords/{landlord_id}", response_model=LandlordResponse)
async def update_landlord(landlord_id: str, landlord_update: LandlordCreate, user: dict = Depends(get_current_user)):
    existing = await db.landlords.find_one({"id": landlord_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    update_dict = landlord_update.model_dump()
    await db.landlords.update_one({"id": landlord_id}, {"$set": update_dict})
    
    updated = await db.landlords.find_one({"id": landlord_id}, {"_id": 0})
    count = await db.properties.count_documents({"landlord_id": landlord_id})
    updated["properties_count"] = count
    return updated

@api_router.delete("/landlords/{landlord_id}")
async def delete_landlord(landlord_id: str, user: dict = Depends(get_current_user)):
    result = await db.landlords.delete_one({"id": landlord_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Landlord not found")
    return {"message": "Landlord deleted successfully"}

# ============ Property Routes ============
@api_router.post("/properties", response_model=PropertyResponse)
async def create_property(property_data: PropertyCreate, user: dict = Depends(get_current_user)):
    landlord = await db.landlords.find_one({"id": property_data.landlord_id}, {"_id": 0})
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    property_dict = property_data.model_dump()
    property_dict["id"] = str(uuid.uuid4())
    property_dict["landlord_name"] = landlord["full_name"]
    property_dict["occupancy_status"] = "vacant"
    property_dict["current_tenants_count"] = 0
    property_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    property_dict["created_by"] = user["id"]
    
    await db.properties.insert_one(property_dict)
    return property_dict

@api_router.get("/properties", response_model=List[PropertyResponse])
async def get_properties(user: dict = Depends(get_current_user)):
    properties = await db.properties.find({}, {"_id": 0}).to_list(1000)
    for prop in properties:
        count = await db.contracts.count_documents({
            "property_id": prop["id"],
            "status": "active"
        })
        prop["current_tenants_count"] = count
        prop["occupancy_status"] = "occupied" if count > 0 else "vacant"
    return properties

@api_router.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: str, user: dict = Depends(get_current_user)):
    prop = await db.properties.find_one({"id": property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    count = await db.contracts.count_documents({
        "property_id": property_id,
        "status": "active"
    })
    prop["current_tenants_count"] = count
    prop["occupancy_status"] = "occupied" if count > 0 else "vacant"
    return prop

@api_router.put("/properties/{property_id}", response_model=PropertyResponse)
async def update_property(property_id: str, property_update: PropertyCreate, user: dict = Depends(get_current_user)):
    existing = await db.properties.find_one({"id": property_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Property not found")
    
    landlord = await db.landlords.find_one({"id": property_update.landlord_id}, {"_id": 0})
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    update_dict = property_update.model_dump()
    update_dict["landlord_name"] = landlord["full_name"]
    await db.properties.update_one({"id": property_id}, {"$set": update_dict})
    
    updated = await db.properties.find_one({"id": property_id}, {"_id": 0})
    count = await db.contracts.count_documents({
        "property_id": property_id,
        "status": "active"
    })
    updated["current_tenants_count"] = count
    updated["occupancy_status"] = "occupied" if count > 0 else "vacant"
    return updated

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str, user: dict = Depends(get_current_user)):
    result = await db.properties.delete_one({"id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}

# ============ Contract Routes ============
@api_router.post("/contracts", response_model=ContractResponse)
async def create_contract(contract: ContractCreate, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": contract.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    property_doc = await db.properties.find_one({"id": contract.property_id}, {"_id": 0})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    
    contract_dict = contract.model_dump()
    contract_dict["id"] = str(uuid.uuid4())
    contract_dict["contract_number"] = f"CNT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    contract_dict["tenant_name"] = tenant["full_name"]
    contract_dict["property_address"] = property_doc["address"]
    contract_dict["status"] = "active"
    contract_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    contract_dict["created_by"] = user["id"]
    
    await db.contracts.insert_one(contract_dict)
    
    # Update tenant's current property
    await db.tenants.update_one(
        {"id": contract.tenant_id},
        {"$set": {"current_property": contract.property_id}}
    )
    
    return contract_dict

@api_router.get("/contracts", response_model=List[ContractResponse])
async def get_contracts(user: dict = Depends(get_current_user)):
    contracts = await db.contracts.find({}, {"_id": 0}).to_list(1000)
    return contracts

@api_router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: str, user: dict = Depends(get_current_user)):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@api_router.put("/contracts/{contract_id}/status")
async def update_contract_status(contract_id: str, status: str, user: dict = Depends(get_current_user)):
    if status not in ["active", "expired", "cancelled", "renewed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {"message": "Contract status updated successfully"}

@api_router.get("/contracts/{contract_id}/pdf")
async def generate_contract_pdf(contract_id: str, user: dict = Depends(get_current_user)):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1D4ED8'),
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("RENTAL CONTRACT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Contract details
    data = [
        ["Contract Number:", contract['contract_number']],
        ["Tenant Name:", contract['tenant_name']],
        ["Property Address:", contract['property_address']],
        ["Start Date:", contract['start_date']],
        ["End Date:", contract['end_date']],
        ["Monthly Rent:", f"${contract['rent_amount']:.2f}"],
        ["Deposit Amount:", f"${contract['deposit_amount']:.2f}"],
        ["Status:", contract['status'].upper()],
    ]
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Terms
    elements.append(Paragraph("<b>Terms and Conditions:</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(contract['terms'], styles['BodyText']))
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=contract_{contract['contract_number']}.pdf"
        }
    )

# ============ Invoice Routes ============
@api_router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, user: dict = Depends(get_current_user)):
    tenant = await db.tenants.find_one({"id": invoice.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    property_doc = await db.properties.find_one({"id": invoice.property_id}, {"_id": 0})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    
    invoice_dict = invoice.model_dump()
    invoice_dict["id"] = str(uuid.uuid4())
    invoice_dict["invoice_number"] = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    invoice_dict["tenant_name"] = tenant["full_name"]
    invoice_dict["property_address"] = property_doc["address"]
    invoice_dict["issue_date"] = datetime.now(timezone.utc).isoformat()
    invoice_dict["payment_status"] = "unpaid"
    invoice_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    invoice_dict["created_by"] = user["id"]
    
    await db.invoices.insert_one(invoice_dict)
    return invoice_dict

@api_router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    """Generate luxury invoice PDF - Consulenze immobiliari style"""
    from invoice_generator import generate_luxury_invoice_pdf
    
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # آماده‌سازی داده برای فاکتور لوکس
    invoice_data = {
        'invoice_number': invoice['invoice_number'].replace('INV-', ''),
        'date': invoice['issue_date'][:10].replace('-', '/'),
        'time': datetime.now(timezone.utc).strftime('%H:%M'),
        'recipient_name': invoice['tenant_name'],
        'amount': invoice['amount'],
        'description': invoice['description'] or f"Affitto di {invoice['invoice_type']}",
        'currency': '€'
    }
    
    # ساخت PDF لوکس
    pdf_buffer = generate_luxury_invoice_pdf(invoice_data)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=ricevuta_{invoice['invoice_number']}.pdf"
        }
    )

# ============ Payment Routes ============
@api_router.post("/payments", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": payment.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment_dict = payment.model_dump()
    payment_dict["id"] = str(uuid.uuid4())
    payment_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    payment_dict["created_by"] = user["id"]
    
    await db.payments.insert_one(payment_dict)
    
    # Update invoice status
    await db.invoices.update_one(
        {"id": payment.invoice_id},
        {"$set": {"payment_status": "paid"}}
    )
    
    # Update tenant's total paid
    tenant_id = invoice["tenant_id"]
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if tenant:
        new_total_paid = tenant.get("total_paid", 0.0) + payment.amount
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"total_paid": new_total_paid}}
        )
    
    return payment_dict

@api_router.get("/payments/tenant/{tenant_id}", response_model=List[PaymentResponse])
async def get_tenant_payments(tenant_id: str, user: dict = Depends(get_current_user)):
    # Get all invoices for this tenant
    invoices = await db.invoices.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(1000)
    invoice_ids = [inv["id"] for inv in invoices]
    
    # Get all payments for these invoices
    payments = await db.payments.find(
        {"invoice_id": {"$in": invoice_ids}},
        {"_id": 0}
    ).to_list(1000)
    
    return payments

# ============ Dashboard Routes ============
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_tenants = await db.tenants.count_documents({})
    total_landlords = await db.landlords.count_documents({})
    total_properties = await db.properties.count_documents({})
    occupied_properties = await db.contracts.count_documents({"status": "active"})
    active_contracts = await db.contracts.count_documents({"status": "active"})
    unpaid_invoices = await db.invoices.count_documents({"payment_status": "unpaid"})
    
    # Calculate total monthly income
    active_contracts_list = await db.contracts.find(
        {"status": "active"},
        {"_id": 0, "rent_amount": 1}
    ).to_list(1000)
    total_monthly_income = sum(c.get("rent_amount", 0) for c in active_contracts_list)
    
    # Calculate total deposits
    tenants_list = await db.tenants.find({}, {"_id": 0, "deposit_amount": 1}).to_list(1000)
    total_deposits = sum(t.get("deposit_amount", 0) for t in tenants_list)
    
    return {
        "total_tenants": total_tenants,
        "total_landlords": total_landlords,
        "total_properties": total_properties,
        "occupied_properties": occupied_properties,
        "vacant_properties": total_properties - occupied_properties,
        "active_contracts": active_contracts,
        "unpaid_invoices": unpaid_invoices,
        "total_monthly_income": total_monthly_income,
        "total_deposits": total_deposits
    }

# ============ Email Routes ============
@api_router.post("/send-email")
async def send_email_endpoint(
    recipient_email: EmailStr,
    subject: str,
    html_content: str,
    user: dict = Depends(get_current_user)
):
    raise HTTPException(status_code=501, detail="Servizio email non ancora configurato. Contattare l'amministratore.")

# Include routers
app.include_router(auth_router)
app.include_router(api_router)

# Import and include Phase 2 routes
try:
    from phase2_routes import router as phase2_router
    app.include_router(phase2_router)
    logger.info("Phase 2 routes loaded successfully")
except Exception as e:
    logger.warning(f"Phase 2 routes not loaded: {e}")

# CORS - must use specific origin with credentials
frontend_url = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
origins = [o.strip() for o in frontend_url.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
