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

# Billing models (stub imports — files exist but are empty; populate in Phase 2)
# from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
# from app.models.payment import Payment, PaymentStatus
# from app.models.discount import Discount
# from app.models.tax import Tax

__all__ = [
    "User",
    "UserRole",
    "UserStatus",
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
]
