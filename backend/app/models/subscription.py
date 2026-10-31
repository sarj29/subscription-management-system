"""
Subscription and SubscriptionLine models with strict status-transition validation.

Subscription status flow:
  draft → quotation → confirmed → active → paused → active
                                         ↘ closed
  confirmed → closed  (if cancelled before activation)
"""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.exceptions import InvalidStatusTransitionError


class SubscriptionStatus(str, enum.Enum):
    DRAFT = "draft"
    QUOTATION = "quotation"      # quote issued, awaiting acceptance
    CONFIRMED = "confirmed"      # accepted, not yet started
    ACTIVE = "active"            # billing is running
    PAUSED = "paused"            # temporarily paused
    CLOSED = "closed"            # terminated


# Valid forward transitions
_SUBSCRIPTION_TRANSITIONS: dict[SubscriptionStatus, set[SubscriptionStatus]] = {
    SubscriptionStatus.DRAFT:      {SubscriptionStatus.QUOTATION, SubscriptionStatus.CLOSED},
    SubscriptionStatus.QUOTATION:  {SubscriptionStatus.CONFIRMED, SubscriptionStatus.CLOSED},
    SubscriptionStatus.CONFIRMED:  {SubscriptionStatus.ACTIVE, SubscriptionStatus.CLOSED},
    SubscriptionStatus.ACTIVE:     {SubscriptionStatus.PAUSED, SubscriptionStatus.CLOSED},
    SubscriptionStatus.PAUSED:     {SubscriptionStatus.ACTIVE, SubscriptionStatus.CLOSED},
    SubscriptionStatus.CLOSED:     set(),
}


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quotation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.DRAFT,
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Denormalized totals (recomputed when lines change)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
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
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="subscriptions"
    )
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")  # noqa: F821
    lines: Mapped[list["SubscriptionLine"]] = relationship(
        "SubscriptionLine",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="SubscriptionLine.position",
    )

    # ------------------------------------------------------------------
    # Status-transition validation
    # ------------------------------------------------------------------
    def transition_status(self, new_status: SubscriptionStatus) -> None:
        """Validate and apply a status transition.

        Raises InvalidStatusTransitionError for invalid transitions.
        """
        current = SubscriptionStatus(self.status)
        allowed = _SUBSCRIPTION_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(current.value, new_status.value)
        self.status = new_status.value

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} status={self.status} total={self.total_amount}>"


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subscription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_variant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("1.0000"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="lines")
    product_variant: Mapped["ProductVariant"] = relationship("ProductVariant")  # noqa: F821

    def __repr__(self) -> str:
        return f"<SubscriptionLine id={self.id} desc={self.description!r} total={self.line_total}>"
