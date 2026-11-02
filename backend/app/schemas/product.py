"""
Pydantic schemas for Product and ProductVariant endpoints.
"""
from decimal import Decimal

from pydantic import BaseModel, Field


class VariantPriceAdjustment(BaseModel):
    adjustment: Decimal = Field(..., description="Amount to add to (or subtract from) variant unit_price")


class ProductVariantBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    sku: str | None = Field(None, max_length=100)
    unit_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sku: str | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    is_active: bool | None = None


class ProductVariantOut(ProductVariantBase):
    id: str
    product_id: str

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    sku: str | None = Field(None, max_length=100)
    is_active: bool = True


class ProductCreate(ProductBase):
    variants: list[ProductVariantCreate] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sku: str | None = None
    is_active: bool | None = None


class ProductOut(ProductBase):
    id: str
    variants: list[ProductVariantOut] = []

    model_config = {"from_attributes": True}
