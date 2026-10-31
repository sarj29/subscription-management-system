"""
Pydantic schemas for Subscription and SubscriptionLine endpoints.
"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.subscription import SubscriptionStatus


class SubscriptionLineBase(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(default=Decimal("1.0000"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    tax_percent: Decimal = Field(default=Decimal("0.00"), ge=0)
    position: int = 0
    product_variant_id: str | None = None


class SubscriptionLineCreate(SubscriptionLineBase):
    pass


class SubscriptionLineOut(SubscriptionLineBase):
    id: str
    subscription_id: str
    line_total: Decimal

    model_config = {"from_attributes": True}


class SubscriptionBase(BaseModel):
    customer_id: str
    plan_id: str
    quotation_id: str | None = None
    reference: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    currency: str = Field(default="USD", max_length=3)


class SubscriptionCreate(SubscriptionBase):
    lines: list[SubscriptionLineCreate] = []


class SubscriptionUpdate(BaseModel):
    reference: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    plan_id: str | None = None
    lines: list[SubscriptionLineCreate] | None = None


class SubscriptionStatusUpdate(BaseModel):
    status: SubscriptionStatus


class SubscriptionRenewal(BaseModel):
    start_date: date | None = None
    notes: str | None = None


class SubscriptionClose(BaseModel):
    reason: str | None = None
    close_date: date | None = None


class SubscriptionOut(SubscriptionBase):
    id: str
    status: SubscriptionStatus
    trial_end_date: date | None = None
    next_billing_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: list[SubscriptionLineOut] = []

    model_config = {"from_attributes": True}
