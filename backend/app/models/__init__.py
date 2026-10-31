"""
Central model registry.

Importing this module guarantees that all ORM models are registered with
``Base.metadata``, which is required for:
  - Alembic autogenerate (``--autogenerate`` flag in ``alembic revision``).
  - Any code that calls ``Base.metadata.create_all(engine)``.

Add every new model file here as it is created.
"""
# Core user / auth
from app.models.user import User, UserRole, UserStatus  # noqa: F401
from app.models.password_reset import PasswordReset  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

# Customers
from app.models.customer import Customer  # noqa: F401

# Products
from app.models.product import Product  # noqa: F401
from app.models.product_variant import ProductVariant  # noqa: F401

# Plans
from app.models.plan import BillingInterval, Plan  # noqa: F401

# Quotations
from app.models.quotation import Quotation, QuotationLine, QuotationStatus  # noqa: F401
from app.models.quotation_template import QuotationTemplate  # noqa: F401

# Subscriptions
from app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus  # noqa: F401

# Discounts
from app.models.discount import Discount, DiscountType  # noqa: F401
from app.models.discount_product import DiscountProduct  # noqa: F401
from app.models.discount_application import DiscountApplication  # noqa: F401

# Taxes
from app.models.tax import Tax  # noqa: F401

# Invoices and Payments
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus  # noqa: F401
from app.models.payment import Payment, PaymentStatus  # noqa: F401

__all__ = [
    "User",
    "UserRole",
    "UserStatus",
    "PasswordReset",
    "AuditLog",
    "Customer",
    "Product",
    "ProductVariant",
    "BillingInterval",
    "Plan",
    "Quotation",
    "QuotationLine",
    "QuotationStatus",
    "QuotationTemplate",
    "Subscription",
    "SubscriptionLine",
    "SubscriptionStatus",
    "Discount",
    "DiscountType",
    "DiscountProduct",
    "DiscountApplication",
    "Tax",
    "Invoice",
    "InvoiceLine",
    "InvoiceStatus",
    "Payment",
    "PaymentStatus",
]
