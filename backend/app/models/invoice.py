"""
Invoice and InvoiceLine models with status transitions and decimal monetary totals.

Invoice status flow:
  draft → confirmed → paid
        ↘ cancelled ↗ (from confirmed)
  paid → cancelled (voiding/cancellation)
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.exceptions import InvalidStatusTransitionError


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"


_INVOICE_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.DRAFT: {InvoiceStatus.CONFIRMED, InvoiceStatus.CANCELLED},
    InvoiceStatus.CONFIRMED: {InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: {InvoiceStatus.CANCELLED},
    InvoiceStatus.CANCELLED: set(),
}


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(InvoiceStatus, name="invoice_status"),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Denormalized totals
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, default=Decimal("0.0000")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, default=Decimal("0.0000")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, default=Decimal("0.0000")
    )
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
    customer: Mapped["Customer"] = relationship("Customer")  # noqa: F821
    subscription: Mapped["Subscription | None"] = relationship("Subscription")  # noqa: F821
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.position",
    )
    payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    def transition_status(self, new_status: InvoiceStatus) -> None:
        """Validate and apply a status transition."""
        current = InvoiceStatus(self.status)
        allowed = _INVOICE_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(current.value, new_status.value)
        self.status = new_status.value
        if new_status == InvoiceStatus.PAID and self.paid_at is None:
            self.paid_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<Invoice id={self.id} number={self.invoice_number!r} status={self.status}>"


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_variant_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, default=Decimal("1.0000")
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0.0000")
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    tax_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, default=Decimal("0.0000")
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    product_variant: Mapped["ProductVariant | None"] = relationship("ProductVariant")  # noqa: F821

    def __repr__(self) -> str:
        return f"<InvoiceLine id={self.id} desc={self.description!r} total={self.line_total}>"
