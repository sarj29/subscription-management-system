"""
Pydantic schemas for Plan endpoints.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.plan import BillingInterval


class PlanBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    interval_count: int = Field(default=1, ge=1)
    base_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    trial_days: int = Field(default=0, ge=0)
    is_active: bool = True

    # Plan configuration settings
    min_quantity: int = Field(default=1, ge=1, description="Minimum quantity required to subscribe")
    available_from: datetime | None = Field(default=None, description="Start date/time plan is available")
    available_until: datetime | None = Field(default=None, description="End date/time plan is available")
    auto_close: bool = Field(default=False, description="Automatically close subscription when end_date arrives")
    allow_pause: bool = Field(default=True, description="Whether customers/staff can pause this plan")
    allow_early_closure: bool = Field(default=True, description="Whether subscription can be terminated early")
    allow_renewal: bool = Field(default=True, description="Whether subscription can be renewed")


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    billing_interval: BillingInterval | None = None
    interval_count: int | None = Field(default=None, ge=1)
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    trial_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    min_quantity: int | None = Field(default=None, ge=1)
    available_from: datetime | None = None
    available_until: datetime | None = None
    auto_close: bool | None = None
    allow_pause: bool | None = None
    allow_early_closure: bool | None = None
    allow_renewal: bool | None = None


class PlanOut(PlanBase):
    id: str

    model_config = {"from_attributes": True}
