"""
DiscountProduct model — junction table linking discounts to eligible products.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DiscountProduct(Base):
    __tablename__ = "discount_products"
    __table_args__ = (
        UniqueConstraint("discount_id", "product_id", name="uq_discount_product"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discount_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    discount: Mapped["Discount"] = relationship(  # noqa: F821
        "Discount", back_populates="discount_products"
    )
    product: Mapped["Product"] = relationship("Product")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DiscountProduct discount_id={self.discount_id} product_id={self.product_id}>"
