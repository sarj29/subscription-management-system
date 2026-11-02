"""
Quotation and QuotationLine models with status-transition validation.

Quotation status flow:
  draft → quotation → confirmed → (subscription created)
                    ↘ expired
  any non-confirmed status → cancelled
"""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base
from app.core.exceptions import InvalidStatusTransitionError


class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    QUOTATION = "quotation"        # sent to customer
    CONFIRMED = "confirmed"        # customer accepted
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Valid forward transitions
_QUOTATION_TRANSITIONS: dict[QuotationStatus, set[QuotationStatus]] = {
    QuotationStatus.DRAFT:      {QuotationStatus.QUOTATION, QuotationStatus.CANCELLED},
    QuotationStatus.QUOTATION:  {QuotationStatus.CONFIRMED, QuotationStatus.EXPIRED, QuotationStatus.CANCELLED},
    QuotationStatus.CONFIRMED:  set(),
    QuotationStatus.EXPIRED:    {QuotationStatus.CANCELLED},
    QuotationStatus.CANCELLED:  set(),
}


class Quotation(Base):
    __tablename__ = "quotations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quotation_templates.id", ondelete="SET NULL"), nullable=True
    )
    reference: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        SAEnum(QuotationStatus, name="quotation_status"),
        nullable=False,
        default=QuotationStatus.DRAFT,
    )
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Totals (denormalized for quick reads; recomputed on line changes)
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
        "Customer", back_populates="quotations"
    )
    template: Mapped["QuotationTemplate"] = relationship(  # noqa: F821
        "QuotationTemplate", back_populates="quotations"
    )
    lines: Mapped[list["QuotationLine"]] = relationship(
        "QuotationLine", back_populates="quotation", cascade="all, delete-orphan", order_by="QuotationLine.position"
    )

    # ------------------------------------------------------------------
    # Status-transition validation
    # ------------------------------------------------------------------
    def transition_status(self, new_status: QuotationStatus) -> None:
        """Validate and apply a status transition.

        Raises InvalidStatusTransitionError if the transition is not permitted.
        """
        current = QuotationStatus(self.status)
        allowed = _QUOTATION_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(current.value, new_status.value)
        self.status = new_status.value

    def __repr__(self) -> str:
        return f"<Quotation id={self.id} status={self.status} total={self.total_amount}>"


class QuotationLine(Base):
    __tablename__ = "quotation_lines"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    quotation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
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
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="lines")
    product_variant: Mapped["ProductVariant"] = relationship("ProductVariant")  # noqa: F821

    def __repr__(self) -> str:
        return f"<QuotationLine id={self.id} desc={self.description!r} total={self.line_total}>"
