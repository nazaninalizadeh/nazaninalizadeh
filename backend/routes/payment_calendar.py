"""Payment Calendar Routes - Monthly payment tracker for tenants."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Payment Calendar"])


@router.get("/payment-calendar/{tenant_id}")
async def get_payment_calendar(tenant_id: str, year: int = 0, user: dict = Depends(get_current_user)):
    """Get monthly payment calendar for a tenant. Returns 12 months with status."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Inquilino non trovato")

    now = datetime.now(timezone.utc)
    if year == 0:
        year = now.year

    due_day = tenant.get("payment_due_day", 5)
    calendar = []

    for month in range(1, 13):
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year + 1}-01-01"
        else:
            month_end = f"{year}-{month + 1:02d}-01"

        payments = await db.payments.find(
            {"tenant_id": tenant_id, "payment_date": {"$gte": month_start, "$lt": month_end}},
            {"_id": 0}
        ).to_list(10)

        total_paid = sum(p.get("amount", 0) for p in payments)
        methods = list(set(p.get("payment_method", "") for p in payments if p.get("payment_method")))

        if payments:
            status = "paid"
        elif year < now.year or (year == now.year and month < now.month):
            status = "late"
        elif year == now.year and month == now.month:
            today = int(now.strftime("%d"))
            status = "late" if today > due_day else "not_paid"
        else:
            status = "not_paid"

        # Only show status for months where tenant was assigned
        created_at = tenant.get("created_at", "")
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if year < created_date.year or (year == created_date.year and month < created_date.month):
                    status = "none"
            except Exception:
                pass

        month_names = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                       "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

        calendar.append({
            "month": month,
            "month_name": month_names[month],
            "year": year,
            "status": status,
            "amount": total_paid,
            "payment_methods": methods,
        })

    return {"tenant_id": tenant_id, "year": year, "calendar": calendar}
