"""
Pydantic schemas for Quotation and QuotationLine endpoints.
"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.quotation import QuotationStatus


class QuotationLineBase(BaseModel):
    description: str
    quantity: Decimal = Decimal("1.0000")
    unit_price: Decimal = Decimal("0.0000")
    discount_percent: Decimal = Decimal("0.00")
    tax_percent: Decimal = Decimal("0.00")
    position: int = 0
    product_variant_id: str | None = None


class QuotationLineCreate(QuotationLineBase):
    pass


class QuotationLineOut(QuotationLineBase):
    id: str
    quotation_id: str
    line_total: Decimal

    model_config = {"from_attributes": True}


class QuotationBase(BaseModel):
    customer_id: str
    template_id: str | None = None
    reference: str | None = None
    valid_until: date | None = None
    notes: str | None = None
    currency: str = "USD"


class QuotationCreate(QuotationBase):
    lines: list[QuotationLineCreate] = []


class QuotationUpdate(BaseModel):
    template_id: str | None = None
    reference: str | None = None
    valid_until: date | None = None
    notes: str | None = None


class QuotationStatusUpdate(BaseModel):
    status: QuotationStatus


class QuotationOut(QuotationBase):
    id: str
    status: QuotationStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: list[QuotationLineOut] = []

    model_config = {"from_attributes": True}
