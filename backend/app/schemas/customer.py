"""
Pydantic schemas for Customer endpoints.
"""
from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    tax_id: str | None = None
    notes: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    tax_id: str | None = None
    notes: str | None = None


class CustomerOut(CustomerBase):
    id: str
    user_id: str | None = None

    model_config = {"from_attributes": True}
