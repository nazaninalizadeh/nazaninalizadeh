"""Notification Routes."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Notifications"])


@router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = []
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")

    overdue = await db.invoices.find({"payment_status": {"$in": ["unpaid", "partial"]}, "due_date": {"$lt": today_str}}, {"_id": 0}).to_list(100)
    for inv in overdue:
        notifications.append({
            "type": "overdue_payment", "severity": "high",
            "title": f"Pagamento scaduto: {inv['tenant_name']}",
            "message": f"Fattura {inv['invoice_number']} di \u20ac{inv['amount']:.2f} scaduta il {inv['due_date']}",
            "tenant_id": inv["tenant_id"], "date": inv["due_date"],
        })

    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming = await db.invoices.find({"payment_status": {"$in": ["unpaid", "partial"]}, "due_date": {"$gte": today_str, "$lte": next_week}}, {"_id": 0}).to_list(100)
    for inv in upcoming:
        notifications.append({
            "type": "upcoming_payment", "severity": "medium",
            "title": f"Pagamento in scadenza: {inv['tenant_name']}",
            "message": f"Fattura {inv['invoice_number']} di \u20ac{inv['amount']:.2f} scade il {inv['due_date']}",
            "tenant_id": inv["tenant_id"], "date": inv["due_date"],
        })

    next_month = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    expiring = await db.contracts.find({"status": "active", "end_date": {"$lte": next_month}}, {"_id": 0}).to_list(100)
    for c in expiring:
        notifications.append({
            "type": "contract_expiry", "severity": "medium",
            "title": f"Contratto in scadenza: {c['tenant_name']}",
            "message": f"Contratto {c['contract_number']} scade il {c['end_date']}",
            "tenant_id": c["tenant_id"], "date": c["end_date"],
        })

    next_90 = (today + timedelta(days=90)).strftime("%Y-%m-%d")
    tenants = await db.tenants.find({"passport_expiry_date": {"$lte": next_90}}, {"_id": 0}).to_list(100)
    for t in tenants:
        notifications.append({
            "type": "passport_expiry", "severity": "low",
            "title": f"Passaporto in scadenza: {t['full_name']}",
            "message": f"Passaporto scade il {t['passport_expiry_date']}",
            "tenant_id": t["id"], "date": t["passport_expiry_date"],
        })

    for t in await db.tenants.find({}, {"_id": 0}).to_list(1000):
        dob = t.get("date_of_birth", "")
        if dob:
            try:
                dob_md = dob[5:]
                today_md = today.strftime("%m-%d")
                if dob_md == today_md:
                    notifications.append({
                        "type": "birthday", "severity": "info",
                        "title": f"Compleanno oggi: {t['full_name']}",
                        "message": f"Auguri a {t['full_name']}!",
                        "tenant_id": t["id"], "date": today_str,
                    })
            except Exception:
                pass

    notifications.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2, "info": 3}.get(x["severity"], 4))
    return notifications


@router.post("/send-email")
async def send_email_endpoint(user: dict = Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Servizio email non ancora configurato.")
