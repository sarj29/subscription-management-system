"""
Pydantic schemas for Quotation and QuotationLine endpoints.
"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.quotation import QuotationStatus


class QuotationLineBase(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(default=Decimal("1.0000"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    tax_percent: Decimal = Field(default=Decimal("0.00"), ge=0)
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
    currency: str = Field(default="USD", max_length=3)


class QuotationCreate(QuotationBase):
    lines: list[QuotationLineCreate] = []


class QuotationUpdate(BaseModel):
    template_id: str | None = None
    reference: str | None = None
    valid_until: date | None = None
    notes: str | None = None
    lines: list[QuotationLineCreate] | None = None


class QuotationStatusUpdate(BaseModel):
    status: QuotationStatus


class QuotationConvertToSubscription(BaseModel):
    plan_id: str = Field(..., description="Target Plan ID for subscription")
    start_date: date | None = None
    notes: str | None = None


class QuotationOut(QuotationBase):
    id: str
    status: QuotationStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: list[QuotationLineOut] = []

    model_config = {"from_attributes": True}
