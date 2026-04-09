from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import os
import base64
from datetime import datetime, timezone, timedelta
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import asyncio
import resend

# Import from main server
from server import db, get_current_user, RESEND_API_KEY, SENDER_EMAIL

router = APIRouter(prefix="/api")

# OCR API Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# ============ Models ============
class PassportOCRResponse(BaseModel):
    full_name: str
    passport_number: str
    nationality: str
    date_of_birth: str
    passport_issue_date: str
    passport_expiry_date: str
    confidence: str

class HospitalityDocCreate(BaseModel):
    tenant_id: str
    property_id: str
    document_type: str
    check_in_date: str
    check_out_date: str
    purpose_of_stay: str

class HospitalityDocResponse(BaseModel):
    id: str
    document_number: str
    tenant_id: str
    tenant_name: str
    property_id: str
    property_address: str
    document_type: str
    check_in_date: str
    check_out_date: str
    purpose_of_stay: str
    created_at: str

class NotificationCreate(BaseModel):
    type: str
    recipient_type: str
    recipient_id: str
    message: str
    scheduled_for: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    action: str
    entity_type: str
    entity_id: str
    changes: dict
    timestamp: str

class ReportRequest(BaseModel):
    report_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    landlord_id: Optional[str] = None

# ============ OCR Passport Extraction ============
@router.post("/tenants/extract-passport", response_model=PassportOCRResponse)
async def extract_passport_info(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Extract passport information using OpenAI Vision"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="OCR service not configured")
    
    try:
        # Read the image
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Initialize OpenAI Vision chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"passport_ocr_{uuid.uuid4()}",
            system_message="You are a passport OCR system. Extract information accurately from passport images."
        ).with_model("openai", "gpt-5.2")
        
        # Create image content
        image_content = ImageContent(image_base64=base64_image)
        
        # Create message with image
        user_message = UserMessage(
            text="""Extract the following information from this passport image and return ONLY a JSON object with these exact fields:
{
  "full_name": "full name as shown",
  "passport_number": "passport number",
  "nationality": "nationality",
  "date_of_birth": "YYYY-MM-DD format",
  "passport_issue_date": "YYYY-MM-DD format",
  "passport_expiry_date": "YYYY-MM-DD format"
}

Return ONLY the JSON, no additional text.""",
            file_contents=[image_content]
        )
        
        # Send message and get response
        response = await chat.send_message(user_message)
        
        # Parse JSON from response
        import json
        try:
            # Extract JSON from response (might have markdown code blocks)
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            extracted_data = json.loads(response_text)
            
            return PassportOCRResponse(
                **extracted_data,
                confidence="high"
            )
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Failed to parse OCR response")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")

# ============ Hospitality Documents ============
@router.post("/hospitality-docs", response_model=HospitalityDocResponse)
async def create_hospitality_document(
    doc: HospitalityDocCreate,
    user: dict = Depends(get_current_user)
):
    """Create hospitality/accommodation document"""
    tenant = await db.tenants.find_one({"id": doc.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    property_doc = await db.properties.find_one({"id": doc.property_id}, {"_id": 0})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    
    doc_dict = doc.model_dump()
    doc_dict["id"] = str(uuid.uuid4())
    doc_dict["document_number"] = f"HSP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    doc_dict["tenant_name"] = tenant["full_name"]
    doc_dict["property_address"] = property_doc["address"]
    doc_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    doc_dict["created_by"] = user["id"]
    
    await db.hospitality_docs.insert_one(doc_dict)
    return doc_dict

@router.get("/hospitality-docs", response_model=List[HospitalityDocResponse])
async def get_hospitality_documents(user: dict = Depends(get_current_user)):
    """Get all hospitality documents"""
    docs = await db.hospitality_docs.find({}, {"_id": 0}).to_list(1000)
    return docs

@router.get("/hospitality-docs/{doc_id}/pdf")
async def generate_hospitality_pdf(doc_id: str, user: dict = Depends(get_current_user)):
    """Generate hospitality document PDF"""
    from fastapi.responses import Response
    
    doc = await db.hospitality_docs.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    buffer = BytesIO()
    pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    from reportlab.lib.styles import ParagraphStyle
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1D4ED8'),
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("ACCOMMODATION CERTIFICATE", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Document details
    data = [
        ["Document Number:", doc['document_number']],
        ["Document Type:", doc['document_type'].upper()],
        ["Guest Name:", doc['tenant_name']],
        ["Property Address:", doc['property_address']],
        ["Check-in Date:", doc['check_in_date']],
        ["Check-out Date:", doc['check_out_date']],
        ["Purpose of Stay:", doc['purpose_of_stay']],
        ["Issue Date:", doc['created_at'][:10]],
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
    
    pdf_doc.build(elements)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=hospitality_{doc['document_number']}.pdf"
        }
    )

# ============ Notifications & Reminders ============
@router.get("/notifications/pending")
async def get_pending_notifications(user: dict = Depends(get_current_user)):
    """Get pending notifications for rent due, contract expiry, passport expiry"""
    notifications = []
    today = datetime.now(timezone.utc).date()
    
    # Check for rent due (next 7 days)
    contracts = await db.contracts.find({"status": "active"}, {"_id": 0}).to_list(1000)
    for contract in contracts:
        # Assuming rent is due monthly on the start date
        start_date = datetime.fromisoformat(contract["start_date"]).date()
        # Calculate next rent due date
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if today.month < 12 else today.year + 1
        rent_due_date = start_date.replace(year=next_year, month=next_month)
        
        days_until_due = (rent_due_date - today).days
        if 0 <= days_until_due <= 7:
            notifications.append({
                "type": "rent_due",
                "priority": "high" if days_until_due <= 3 else "medium",
                "message": f"Rent due in {days_until_due} days for {contract['tenant_name']}",
                "entity_id": contract["id"],
                "entity_type": "contract",
                "due_date": rent_due_date.isoformat()
            })
    
    # Check for contract expiry (next 30 days)
    for contract in contracts:
        end_date = datetime.fromisoformat(contract["end_date"]).date()
        days_until_expiry = (end_date - today).days
        if 0 <= days_until_expiry <= 30:
            notifications.append({
                "type": "contract_expiry",
                "priority": "high" if days_until_expiry <= 7 else "medium",
                "message": f"Contract expires in {days_until_expiry} days for {contract['tenant_name']}",
                "entity_id": contract["id"],
                "entity_type": "contract",
                "expiry_date": end_date.isoformat()
            })
    
    # Check for passport expiry (next 90 days)
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    for tenant in tenants:
        expiry_date = datetime.fromisoformat(tenant["passport_expiry_date"]).date()
        days_until_expiry = (expiry_date - today).days
        if 0 <= days_until_expiry <= 90:
            notifications.append({
                "type": "passport_expiry",
                "priority": "high" if days_until_expiry <= 30 else "low",
                "message": f"Passport expires in {days_until_expiry} days for {tenant['full_name']}",
                "entity_id": tenant["id"],
                "entity_type": "tenant",
                "expiry_date": expiry_date.isoformat()
            })
    
    return {
        "total": len(notifications),
        "notifications": sorted(notifications, key=lambda x: (x["priority"] == "low", x.get("due_date", x.get("expiry_date"))))
    }

# ============ Audit Logs ============
async def create_audit_log(user_id: str, user_name: str, action: str, entity_type: str, entity_id: str, changes: dict):
    """Create an audit log entry"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "changes": changes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(log_entry)

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    entity_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get audit logs"""
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs

# ============ Reports ============
@router.post("/reports/generate")
async def generate_report(
    report_req: ReportRequest,
    user: dict = Depends(get_current_user)
):
    """Generate various reports"""
    
    if report_req.report_type == "monthly_income":
        # Calculate monthly income
        contracts = await db.contracts.find({"status": "active"}, {"_id": 0}).to_list(1000)
        total_monthly = sum(c.get("rent_amount", 0) for c in contracts)
        
        # Group by landlord
        landlord_income = {}
        for contract in contracts:
            property_doc = await db.properties.find_one({"id": contract["property_id"]}, {"_id": 0})
            if property_doc:
                landlord_id = property_doc["landlord_id"]
                landlord_name = property_doc["landlord_name"]
                if landlord_id not in landlord_income:
                    landlord_income[landlord_id] = {
                        "landlord_name": landlord_name,
                        "properties": 0,
                        "monthly_income": 0
                    }
                landlord_income[landlord_id]["properties"] += 1
                landlord_income[landlord_id]["monthly_income"] += contract["rent_amount"]
        
        return {
            "report_type": "monthly_income",
            "total_monthly_income": total_monthly,
            "landlord_breakdown": list(landlord_income.values()),
            "active_contracts": len(contracts),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    elif report_req.report_type == "outstanding_payments":
        # Get unpaid invoices
        unpaid = await db.invoices.find({"payment_status": "unpaid"}, {"_id": 0}).to_list(1000)
        total_outstanding = sum(inv.get("amount", 0) for inv in unpaid)
        
        # Group by tenant
        tenant_outstanding = {}
        for invoice in unpaid:
            tenant_id = invoice["tenant_id"]
            tenant_name = invoice["tenant_name"]
            if tenant_id not in tenant_outstanding:
                tenant_outstanding[tenant_id] = {
                    "tenant_name": tenant_name,
                    "invoices": 0,
                    "total_amount": 0
                }
            tenant_outstanding[tenant_id]["invoices"] += 1
            tenant_outstanding[tenant_id]["total_amount"] += invoice["amount"]
        
        return {
            "report_type": "outstanding_payments",
            "total_outstanding": total_outstanding,
            "unpaid_invoices_count": len(unpaid),
            "tenant_breakdown": list(tenant_outstanding.values()),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    elif report_req.report_type == "occupancy":
        # Calculate occupancy rate
        properties = await db.properties.find({}, {"_id": 0}).to_list(1000)
        total_properties = len(properties)
        occupied = sum(1 for p in properties if p.get("occupancy_status") == "occupied")
        vacant = total_properties - occupied
        
        occupancy_rate = (occupied / total_properties * 100) if total_properties > 0 else 0
        
        return {
            "report_type": "occupancy",
            "total_properties": total_properties,
            "occupied": occupied,
            "vacant": vacant,
            "occupancy_rate": round(occupancy_rate, 2),
            "properties_breakdown": [
                {
                    "property_code": p["property_code"],
                    "address": p["address"],
                    "status": p["occupancy_status"],
                    "tenants": p.get("current_tenants_count", 0),
                    "capacity": p["capacity"]
                }
                for p in properties
            ],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    elif report_req.report_type == "deposit_summary":
        # Calculate deposits
        tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
        total_deposits = sum(t.get("deposit_amount", 0) for t in tenants)
        total_paid = sum(t.get("total_paid", 0) for t in tenants)
        
        return {
            "report_type": "deposit_summary",
            "total_deposits": total_deposits,
            "total_paid": total_paid,
            "outstanding": total_deposits - total_paid,
            "tenant_count": len(tenants),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
