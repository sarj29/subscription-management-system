"""
Pydantic schemas for Product and ProductVariant endpoints.
"""
from decimal import Decimal

from pydantic import BaseModel


class ProductVariantBase(BaseModel):
    name: str
    description: str | None = None
    sku: str | None = None
    unit_price: Decimal = Decimal("0.0000")
    currency: str = "USD"
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sku: str | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    is_active: bool | None = None


class ProductVariantOut(ProductVariantBase):
    id: str
    product_id: str

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    sku: str | None = None
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
