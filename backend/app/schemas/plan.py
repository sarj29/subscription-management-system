"""
Pydantic schemas for Plan endpoints.
"""
from decimal import Decimal

from pydantic import BaseModel

from app.models.plan import BillingInterval


class PlanBase(BaseModel):
    name: str
    description: str | None = None
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    interval_count: int = 1
    base_price: Decimal = Decimal("0.0000")
    currency: str = "USD"
    trial_days: int = 0
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    billing_interval: BillingInterval | None = None
    interval_count: int | None = None
    base_price: Decimal | None = None
    currency: str | None = None
    trial_days: int | None = None
    is_active: bool | None = None


class PlanOut(PlanBase):
    id: str

    model_config = {"from_attributes": True}
