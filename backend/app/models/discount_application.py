"""
DiscountApplication model — records discounts applied to quotations, subscriptions, or invoices.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DiscountApplication(Base):
    __tablename__ = "discount_applications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discount_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quotation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quotations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    subscription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True
    )
    amount_saved: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    discount: Mapped["Discount"] = relationship(  # noqa: F821
        "Discount", back_populates="applications"
    )
    quotation: Mapped["Quotation | None"] = relationship("Quotation")  # noqa: F821
    subscription: Mapped["Subscription | None"] = relationship("Subscription")  # noqa: F821
    invoice: Mapped["Invoice | None"] = relationship("Invoice")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<DiscountApplication id={self.id} "
            f"discount_id={self.discount_id} "
            f"saved={self.amount_saved} {self.currency}>"
        )
