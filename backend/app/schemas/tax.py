"""
Pydantic schemas for Tax endpoints.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TaxBase(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    country: str | None = None
    description: str | None = None
    is_active: bool = True


class TaxCreate(TaxBase):
    pass


class TaxUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    rate: Decimal | None = Field(default=None, ge=0)
    country: str | None = None
    description: str | None = None
    is_active: bool | None = None


class TaxOut(TaxBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
