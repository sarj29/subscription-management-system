"""
Pydantic schemas for Discount, DiscountProduct, and DiscountApplication.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.discount import DiscountType


class DiscountProductBase(BaseModel):
    product_id: str


class DiscountProductCreate(DiscountProductBase):
    pass


class DiscountProductOut(DiscountProductBase):
    id: str
    discount_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DiscountBase(BaseModel):
    code: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    discount_type: DiscountType = DiscountType.PERCENTAGE
    value: Decimal = Field(default=Decimal("0.0000"), ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    active_from: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True


class DiscountCreate(DiscountBase):
    product_ids: list[str] = []


class DiscountUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    discount_type: DiscountType | None = None
    value: Decimal | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    active_from: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
    product_ids: list[str] | None = None


class DiscountOut(DiscountBase):
    id: str
    used_count: int
    created_at: datetime
    updated_at: datetime
    discount_products: list[DiscountProductOut] = []

    model_config = {"from_attributes": True}


class DiscountApplicationBase(BaseModel):
    discount_id: str
    quotation_id: str | None = None
    subscription_id: str | None = None
    invoice_id: str | None = None
    amount_saved: Decimal = Field(default=Decimal("0.0000"), ge=0)
    currency: str = "USD"


class DiscountApplicationCreate(DiscountApplicationBase):
    pass


class DiscountApplicationOut(DiscountApplicationBase):
    id: str
    applied_at: datetime

    model_config = {"from_attributes": True}
