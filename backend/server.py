"""
PropertyOps - Consulenze immobiliari
Main application entry point.
Modular architecture with separated routes, services, and models.
"""

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / '.env')

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging

from database import db, client
from auth import auth_router, seed_admins

# Route modules
from routes.tenants import router as tenants_router
from routes.landlords import router as landlords_router
from routes.properties import router as properties_router
from routes.rooms import router as rooms_router
from routes.contracts import router as contracts_router
from routes.invoices import router as invoices_router
from routes.payments import router as payments_router
from routes.documents import router as documents_router
from routes.dashboard import router as dashboard_router
from routes.reports import router as reports_router
from routes.notifications_routes import router as notifications_router
from routes.ocr import router as ocr_router
from routes.hospitality import router as hospitality_router
from routes.data_exchange import router as data_exchange_router
from routes.ricevuta import router as ricevuta_router
from routes.registration import router as registration_router
from routes.payment_calendar import router as payment_calendar_router

app = FastAPI(title="PropertyOps API", version="2.0.0")

# Upload directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "documents").mkdir(exist_ok=True)
(UPLOAD_DIR / "rooms").mkdir(exist_ok=True)

# Serve uploaded files (under /api/* so Kubernetes ingress routes them to the backend
# instead of falling through to the frontend, which would Navigate to /)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ============ Startup ============
@app.on_event("startup")
async def startup_event():
    await db.tenants.create_index("passport_number")
    await db.properties.create_index("property_code")
    await db.contracts.create_index("contract_number")
    await db.invoices.create_index("invoice_number")
    await db.rooms.create_index("property_id")
    await db.payments.create_index("tenant_id")
    await db.documents.create_index("owner_id")
    await db.ocr_scans.create_index("id")
    await db.monthly_status.create_index([("tenant_id", 1), ("month", 1), ("year", 1)], unique=True)
    await seed_admins()
    # Migrate any pre-existing /uploads/ URLs in the DB to the new /api/uploads/ prefix.
    # Without /api prefix the Kubernetes ingress routes the request to the frontend,
    # which then redirects to "/" (Dashboard) — breaking document downloads.
    await _migrate_upload_urls()


async def _migrate_upload_urls():
    # Documents collection: single `url` string field
    async for doc in db.documents.find({"url": {"$regex": "^/uploads/"}}, {"_id": 1, "url": 1}):
        await db.documents.update_one(
            {"_id": doc["_id"]},
            {"$set": {"url": "/api" + doc["url"]}},
        )
    # Rooms / properties: `images` array
    for coll in (db.rooms, db.properties):
        async for d in coll.find({"images": {"$elemMatch": {"$regex": "^/uploads/"}}}, {"_id": 1, "images": 1}):
            new_imgs = [("/api" + u) if isinstance(u, str) and u.startswith("/uploads/") else u for u in (d.get("images") or [])]
            await coll.update_one({"_id": d["_id"]}, {"$set": {"images": new_imgs}})
    # Tenants: profile_photo and any embedded URLs
    async for t in db.tenants.find({"profile_photo": {"$regex": "^/uploads/"}}, {"_id": 1, "profile_photo": 1}):
        await db.tenants.update_one({"_id": t["_id"]}, {"$set": {"profile_photo": "/api" + t["profile_photo"]}})

# ============ Include All Routers ============
app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(landlords_router)
app.include_router(properties_router)
app.include_router(rooms_router)
app.include_router(contracts_router)
app.include_router(invoices_router)
app.include_router(payments_router)
app.include_router(documents_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(notifications_router)
app.include_router(ocr_router)
app.include_router(hospitality_router)
app.include_router(data_exchange_router)
app.include_router(ricevuta_router)
app.include_router(registration_router)
app.include_router(payment_calendar_router)

# ============ CORS ============
frontend_url = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
origins = [o.strip() for o in frontend_url.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Logging ============
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
