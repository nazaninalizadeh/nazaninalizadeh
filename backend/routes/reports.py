"""Report Routes."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from io import BytesIO
from datetime import datetime, timezone, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch, cm

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/reports/generate")
async def generate_report(
    report_type: str = Query("monthly"),
    period: str = Query(""),
    user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    if report_type == "weekly":
        start = (now - timedelta(days=7)).isoformat()
    elif report_type == "monthly":
        start = (now - timedelta(days=30)).isoformat()
    elif report_type == "yearly":
        start = (now - timedelta(days=365)).isoformat()
    else:
        start = (now - timedelta(days=30)).isoformat()

    payments = await db.payments.find({"created_at": {"$gte": start}}, {"_id": 0}).to_list(5000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(1000)

    total_received = sum(p.get("amount", 0) for p in payments)
    unpaid = [i for i in invoices if i.get("payment_status") in ["unpaid", "partial"]]
    partial = [i for i in invoices if i.get("payment_status") == "partial"]
    today = now.strftime("%Y-%m-%d")
    overdue = [i for i in unpaid if i.get("due_date", "9999") < today]
    occupied = sum(1 for r in rooms if r.get("status") == "occupied")

    tenant_balances = []
    for t in tenants:
        bal = t.get("total_due", 0) - t.get("total_paid", 0)
        if bal > 0:
            tenant_balances.append({"name": t["full_name"], "balance": bal})

    return {
        "report_type": report_type,
        "generated_at": now.isoformat(),
        "period_start": start,
        "summary": {
            "total_payments_received": total_received,
            "payment_count": len(payments),
            "unpaid_invoices": len(unpaid),
            "partial_payments": len(partial),
            "overdue_invoices": len(overdue),
            "total_overdue_amount": sum(i.get("amount", 0) - i.get("paid_amount", 0) for i in overdue),
            "total_rooms": len(rooms),
            "occupied_rooms": occupied,
            "vacant_rooms": len(rooms) - occupied,
            "occupancy_rate": round(occupied / max(len(rooms), 1) * 100, 1),
        },
        "tenant_balances": sorted(tenant_balances, key=lambda x: -x["balance"]),
        "recent_payments": payments[:20],
        "overdue_details": overdue[:20],
    }


@router.get("/reports/pdf")
async def generate_report_pdf(
    report_type: str = Query("monthly"),
    user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    if report_type == "weekly":
        start = now - timedelta(days=7)
        title = "Report Settimanale"
    elif report_type == "yearly":
        start = now - timedelta(days=365)
        title = "Report Annuale"
    else:
        start = now - timedelta(days=30)
        title = "Report Mensile"

    payments = await db.payments.find({"created_at": {"$gte": start.isoformat()}}, {"_id": 0}).to_list(5000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(5000)
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(1000)
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(1000)

    total_received = sum(p.get("amount", 0) for p in payments)
    unpaid = [i for i in invoices if i.get("payment_status") in ["unpaid", "partial"]]
    occupied = sum(1 for r in rooms if r.get("status") == "occupied")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1 * cm, bottomMargin=1 * cm)
    styles = getSampleStyleSheet()
    elems = []

    h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#9F1239'), alignment=1)
    elems.append(Paragraph(f"Consulenze immobiliari - {title}", h1))
    elems.append(Paragraph(f"Periodo: {start.strftime('%d/%m/%Y')} - {now.strftime('%d/%m/%Y')}", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1, textColor=colors.grey)))
    elems.append(Spacer(1, 0.4 * inch))

    summary_data = [
        ["Metrica", "Valore"],
        ["Pagamenti Ricevuti", f"\u20ac{total_received:,.2f}"],
        ["N. Pagamenti", str(len(payments))],
        ["Fatture Non Pagate", str(len(unpaid))],
        ["Stanze Totali", str(len(rooms))],
        ["Stanze Occupate", str(occupied)],
        ["Stanze Libere", str(len(rooms) - occupied)],
        ["Tasso Occupazione", f"{round(occupied / max(len(rooms), 1) * 100, 1)}%"],
    ]
    t = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9F1239')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF7ED')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.3 * inch))

    elems.append(Paragraph("<b>Saldi Inquilini</b>", styles['Heading3']))
    bal_data = [["Inquilino", "Dovuto", "Pagato", "Saldo"]]
    for ten in tenants:
        due = ten.get("total_due", 0)
        paid = ten.get("total_paid", 0)
        bal = due - paid
        if due > 0 or paid > 0:
            bal_data.append([ten["full_name"], f"\u20ac{due:,.2f}", f"\u20ac{paid:,.2f}", f"\u20ac{bal:,.2f}"])
    if len(bal_data) > 1:
        bt = Table(bal_data, colWidths=[5 * cm, 3.5 * cm, 3.5 * cm, 4 * cm])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9F1239')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(bt)
    else:
        elems.append(Paragraph("Nessun dato disponibile", styles['Normal']))

    doc.build(elems)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=report_{report_type}_{now.strftime('%Y%m%d')}.pdf"})
