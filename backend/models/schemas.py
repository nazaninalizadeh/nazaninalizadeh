from pydantic import BaseModel, EmailStr
from typing import Optional


class TenantCreate(BaseModel):
    full_name: str
    codice_fiscale: Optional[str] = ""
    passport_number: str
    nationality: str
    date_of_birth: str
    passport_issue_date: str
    passport_expiry_date: str
    id_type: Optional[str] = ""
    id_number: Optional[str] = ""
    phone: str
    email: EmailStr
    whatsapp: str
    address: str
    occupation: str
    notes: Optional[str] = ""
    deposit_amount: float = 0.0
    property_id: Optional[str] = ""
    room_id: Optional[str] = ""


class LandlordCreate(BaseModel):
    full_name: str
    codice_fiscale: Optional[str] = ""
    phone: str
    email: EmailStr
    whatsapp: str
    id_type: Optional[str] = ""
    id_number: str
    bank_details: str
    notes: Optional[str] = ""


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


class RoomCreate(BaseModel):
    property_id: str
    room_number: str
    room_type: str
    floor: Optional[str] = ""
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
    tenant_id: str
    property_id: str
    contract_id: str
    invoice_type: str
    amount: float
    due_date: str
    description: str


class PaymentCreate(BaseModel):
    invoice_id: Optional[str] = ""
    tenant_id: str
    amount: float
    payment_method: str
    payment_date: str
    notes: Optional[str] = ""
