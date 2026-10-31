"""
Payment model with recorded/reversed status workflow and monetary tracking.

Payment status flow:
  recorded → reversed
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.exceptions import InvalidStatusTransitionError


class PaymentStatus(str, enum.Enum):
    RECORDED = "recorded"
    REVERSED = "reversed"


_PAYMENT_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.RECORDED: {PaymentStatus.REVERSED},
    PaymentStatus.REVERSED: set(),
}


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_number: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )
    transaction_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.RECORDED,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reversed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")  # noqa: F821
    customer: Mapped["Customer"] = relationship("Customer")  # noqa: F821

    def transition_status(self, new_status: PaymentStatus) -> None:
        """Validate and apply a status transition."""
        current = PaymentStatus(self.status)
        allowed = _PAYMENT_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(current.value, new_status.value)
        self.status = new_status.value
        if new_status == PaymentStatus.REVERSED and self.reversed_at is None:
            self.reversed_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} "
            f"amount={self.amount} {self.currency} "
            f"status={self.status}>"
        )
