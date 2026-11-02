"""
Pydantic schemas for Payment endpoints.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.payment import PaymentStatus


class PaymentBase(BaseModel):
    invoice_id: str
    customer_id: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    payment_method: str = "manual"
    transaction_reference: str | None = None
    notes: str | None = None


class PaymentCreate(PaymentBase):
    payment_number: str | None = None


class PaymentUpdate(BaseModel):
    payment_method: str | None = None
    transaction_reference: str | None = None
    notes: str | None = None


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus


class PaymentOut(PaymentBase):
    id: str
    payment_number: str | None = None
    status: PaymentStatus
    recorded_at: datetime
    reversed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
