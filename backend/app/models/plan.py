"""
Plan model — represents a subscription tier (e.g. Basic, Pro, Enterprise).
One Plan can have many Subscriptions.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

import enum


class BillingInterval(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_interval: Mapped[str] = mapped_column(
        SAEnum(BillingInterval, name="billing_interval"),
        nullable=False,
        default=BillingInterval.MONTHLY,
    )
    # How many units of billing_interval between charges (e.g. 3 = every 3 months)
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    base_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    trial_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="plan"
    )

    def __repr__(self) -> str:
        return f"<Plan id={self.id} name={self.name} interval={self.billing_interval}>"
