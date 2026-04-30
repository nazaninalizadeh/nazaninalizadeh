from pydantic import BaseModel, EmailStr
from typing import Optional
import random
import string


def generate_property_code():
    """Generate a random unique property code like IMM-A3X7."""
    chars = random.choices(string.ascii_uppercase + string.digits, k=4)
    return f"IMM-{''.join(chars)}"


class TenantCreate(BaseModel):
    full_name: str
    codice_fiscale: Optional[str] = ""
    passport_number: str
    nationality: str
    date_of_birth: str
    place_of_birth: Optional[str] = ""
    country_of_birth: Optional[str] = ""
    passport_issue_date: str
    passport_expiry_date: str
    id_type: Optional[str] = ""
    id_number: Optional[str] = ""
    issuing_authority: Optional[str] = ""  # from OCR: document authority
    phone: Optional[str] = ""
    email: EmailStr
    whatsapp: Optional[str] = ""  # legacy: kept optional for back-compat
    notes: Optional[str] = ""
    deposit_amount: float = 0.0
    property_id: Optional[str] = ""
    room_id: Optional[str] = ""
    payment_due_day: int = 5
    address: Optional[str] = ""


class LandlordCreate(BaseModel):
    full_name: str
    codice_fiscale: Optional[str] = ""
    phone: str
    email: EmailStr
    whatsapp: Optional[str] = ""  # legacy: kept optional for back-compat
    id_type: Optional[str] = ""
    id_number: str
    authority: Optional[str] = ""  # issuing authority (from OCR)
    bank_details: str
    notes: Optional[str] = ""
    date_of_birth: Optional[str] = ""
    place_of_birth: Optional[str] = ""
    province_of_birth: Optional[str] = ""
    country_of_birth: Optional[str] = ""
    residence: Optional[str] = ""
    signature_url: Optional[str] = ""


class PropertyCreate(BaseModel):
    property_code: Optional[str] = ""
    address: str
    civico: Optional[str] = ""           # numero civico (street number)
    comune: Optional[str] = ""           # comune (city)
    property_type: str = "Appartamento"
    number_of_rooms: int
    capacity: int
    landlord_id: str
    rental_amount: float
    additional_charges: Optional[str] = ""
    province: Optional[str] = "PD"
    phone: Optional[str] = ""


class RoomCreate(BaseModel):
    property_id: str
    room_number: str
    room_type: str
    monthly_rent: float = 0.0
    description: Optional[str] = ""
    bill_responsible: Optional[str] = ""


class ContractCreate(BaseModel):
    tenant_id: str
    property_id: str
    room_id: Optional[str] = ""
    start_date: str
    end_date: str
    rent_amount: float
    deposit_amount: float
    terms: str


class InvoiceCreate(BaseModel):
    tenant_id: Optional[str] = ""
    property_id: Optional[str] = ""
    contract_id: Optional[str] = ""
    invoice_type: str
    amount: float
    due_date: str
    description: str
    document_type: Optional[str] = "fattura"  # "fattura" or "preavviso"
    # breakdown + recipient overrides (optional — if not set, tenant data is used)
    rent: Optional[float] = 0.0
    deposit: Optional[float] = 0.0
    agency_fee: Optional[float] = 0.0
    registration: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    vat_rate: Optional[float] = 22.0
    # preavviso-specific
    imponibile: Optional[float] = 0.0
    rimborso_label: Optional[str] = ""
    rimborso_amount: Optional[float] = 0.0
    rimborso_note: Optional[str] = ""
    rimborso_tax_note: Optional[str] = ""
    body_text: Optional[str] = ""
    # recipient overrides (for commercial clients — e.g. ELEISON)
    recipient_name: Optional[str] = ""
    recipient_address: Optional[str] = ""
    recipient_cf_piva: Optional[str] = ""
    recipient_city: Optional[str] = ""


class PaymentCreate(BaseModel):
    invoice_id: Optional[str] = ""
    tenant_id: str
    amount: float
    payment_method: str
    payment_date: str
    notes: Optional[str] = ""
