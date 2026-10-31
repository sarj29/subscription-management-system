"""
Pydantic schemas registry.
"""
from app.schemas.audit_log import AuditLogBase, AuditLogCreate, AuditLogOut  # noqa: F401
from app.schemas.auth import (  # noqa: F401
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.schemas.customer import (  # noqa: F401
    CustomerBase,
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
)
from app.schemas.discount import (  # noqa: F401
    DiscountApplicationBase,
    DiscountApplicationCreate,
    DiscountApplicationOut,
    DiscountBase,
    DiscountCreate,
    DiscountOut,
    DiscountProductBase,
    DiscountProductCreate,
    DiscountProductOut,
    DiscountUpdate,
)
from app.schemas.invoice import (  # noqa: F401
    InvoiceBase,
    InvoiceCreate,
    InvoiceLineBase,
    InvoiceLineCreate,
    InvoiceLineOut,
    InvoiceLineUpdate,
    InvoiceOut,
    InvoiceStatusUpdate,
    InvoiceUpdate,
)
from app.schemas.password_reset import (  # noqa: F401
    PasswordResetConfirm,
    PasswordResetOut,
    PasswordResetRequest,
)
from app.schemas.payment import (  # noqa: F401
    PaymentBase,
    PaymentCreate,
    PaymentOut,
    PaymentStatusUpdate,
    PaymentUpdate,
)
from app.schemas.plan import PlanBase, PlanCreate, PlanOut, PlanUpdate  # noqa: F401
from app.schemas.product import (  # noqa: F401
    ProductBase,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductVariantBase,
    ProductVariantCreate,
    ProductVariantOut,
    ProductVariantUpdate,
    VariantPriceAdjustment,
)
from app.schemas.quotation import (  # noqa: F401
    QuotationBase,
    QuotationConvertToSubscription,
    QuotationCreate,
    QuotationLineBase,
    QuotationLineCreate,
    QuotationLineOut,
    QuotationOut,
    QuotationStatusUpdate,
    QuotationUpdate,
)
from app.schemas.subscription import (  # noqa: F401
    SubscriptionBase,
    SubscriptionClose,
    SubscriptionCreate,
    SubscriptionLineBase,
    SubscriptionLineCreate,
    SubscriptionLineOut,
    SubscriptionOut,
    SubscriptionRenewal,
    SubscriptionStatusUpdate,
    SubscriptionUpdate,
)
from app.schemas.tax import TaxBase, TaxCreate, TaxOut, TaxUpdate  # noqa: F401
