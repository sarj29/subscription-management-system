"""
Pydantic schemas for Invoice and InvoiceLine endpoints.
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.invoice import InvoiceStatus


class InvoiceLineBase(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(default=Decimal("1.0000"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    tax_percent: Decimal = Field(default=Decimal("0.00"), ge=0)
    position: int = 0
    product_variant_id: str | None = None


class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLineUpdate(BaseModel):
    description: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    tax_percent: Decimal | None = Field(default=None, ge=0)
    position: int | None = None
    product_variant_id: str | None = None


class InvoiceLineOut(InvoiceLineBase):
    id: str
    invoice_id: str
    line_total: Decimal

    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    customer_id: str
    subscription_id: str | None = None
    invoice_number: str | None = None
    issue_date: date | None = None
    due_date: date
    notes: str | None = None
    currency: str = "USD"


class InvoiceCreate(InvoiceBase):
    lines: list[InvoiceLineCreate] = []


class InvoiceUpdate(BaseModel):
    due_date: date | None = None
    notes: str | None = None


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceOut(InvoiceBase):
    id: str
    invoice_number: str
    status: InvoiceStatus
    issue_date: date
    paid_at: datetime | None = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: list[InvoiceLineOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
