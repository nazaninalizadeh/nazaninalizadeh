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

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

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
    await seed_admins()

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
