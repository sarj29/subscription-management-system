"""
Unit tests for Phase 2 SQLAlchemy models and Pydantic schemas.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import InvalidStatusTransitionError
from app.models import (
    AuditLog,
    Customer,
    Discount,
    DiscountApplication,
    DiscountProduct,
    DiscountType,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    PasswordReset,
    Payment,
    PaymentStatus,
    Plan,
    Product,
    ProductVariant,
    Quotation,
    QuotationLine,
    QuotationStatus,
    QuotationTemplate,
    Subscription,
    SubscriptionLine,
    SubscriptionStatus,
    Tax,
    User,
    UserRole,
    UserStatus,
)
from app.schemas import (
    AuditLogCreate,
    AuditLogOut,
    DiscountApplicationCreate,
    DiscountApplicationOut,
    DiscountCreate,
    DiscountOut,
    DiscountProductOut,
    DiscountUpdate,
    InvoiceCreate,
    InvoiceLineCreate,
    InvoiceLineOut,
    InvoiceOut,
    InvoiceStatusUpdate,
    InvoiceUpdate,
    PasswordResetConfirm,
    PasswordResetOut,
    PasswordResetRequest,
    PaymentCreate,
    PaymentOut,
    PaymentStatusUpdate,
    PaymentUpdate,
    TaxCreate,
    TaxOut,
    TaxUpdate,
)


@pytest.fixture
def db_session():
    """Provides a fresh in-memory SQLite session for testing models."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_base_metadata_contains_all_models():
    """Verify Base.metadata has registered all 19 tables."""
    expected_tables = {
        "users",
        "password_resets",
        "audit_logs",
        "customers",
        "products",
        "product_variants",
        "plans",
        "quotations",
        "quotation_lines",
        "quotation_templates",
        "subscriptions",
        "subscription_lines",
        "discounts",
        "discount_products",
        "discount_applications",
        "taxes",
        "invoices",
        "invoice_lines",
        "payments",
    }
    registered = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered), f"Missing tables: {expected_tables - registered}"


def test_password_reset_model(db_session):
    """Verify PasswordReset model structure and persistence defaults."""
    reset = PasswordReset(
        user_id=str(uuid.uuid4()),
        token_hash="samplehash123",
        expires_at=datetime.now(timezone.utc),
    )
    assert reset.is_used is False
    reset.used_at = datetime.now(timezone.utc)
    assert reset.is_used is True

    db_session.add(reset)
    db_session.commit()
    assert reset.id is not None
    assert len(reset.id) == 36


def test_audit_log_model(db_session):
    """Verify AuditLog model structure and persistence."""
    log = AuditLog(
        action="invoice.created",
        entity_type="Invoice",
        entity_id=str(uuid.uuid4()),
        details={"invoice_number": "INV-001"},
    )
    assert log.action == "invoice.created"
    assert "Invoice" in repr(log)

    db_session.add(log)
    db_session.commit()
    assert log.id is not None
    assert len(log.id) == 36


def test_tax_model(db_session):
    """Verify Tax model structure and persistence."""
    tax = Tax(
        name="VAT 20%",
        code="VAT-20",
        rate=Decimal("0.2000"),
        country="US",
    )
    assert tax.rate == Decimal("0.2000")

    db_session.add(tax)
    db_session.commit()
    assert tax.id is not None
    assert tax.is_active is True


def test_discount_models(db_session):
    """Verify Discount, DiscountProduct, and DiscountApplication models."""
    discount = Discount(
        code="SUMMER25",
        name="Summer 25% Off",
        discount_type=DiscountType.PERCENTAGE,
        value=Decimal("25.0000"),
    )
    db_session.add(discount)
    db_session.commit()

    assert discount.id is not None
    assert discount.is_active is True
    assert discount.used_count == 0

    dp = DiscountProduct(
        discount_id=discount.id,
        product_id=str(uuid.uuid4()),
    )
    db_session.add(dp)
    db_session.commit()
    assert dp.id is not None

    app = DiscountApplication(
        discount_id=discount.id,
        amount_saved=Decimal("50.0000"),
        currency="USD",
    )
    db_session.add(app)
    db_session.commit()
    assert app.id is not None
    assert app.amount_saved == Decimal("50.0000")


def test_invoice_model_and_transitions(db_session):
    """Verify Invoice lifecycle, status transitions, and persistence."""
    inv = Invoice(
        invoice_number="INV-2026-001",
        customer_id=str(uuid.uuid4()),
        due_date=date(2026, 11, 30),
        status=InvoiceStatus.DRAFT.value,
    )
    assert inv.status == InvoiceStatus.DRAFT.value
    assert inv.paid_at is None

    db_session.add(inv)
    db_session.commit()
    assert inv.id is not None
    assert inv.currency == "USD"

    # draft -> confirmed
    inv.transition_status(InvoiceStatus.CONFIRMED)
    assert inv.status == InvoiceStatus.CONFIRMED.value

    # confirmed -> paid
    inv.transition_status(InvoiceStatus.PAID)
    assert inv.status == InvoiceStatus.PAID.value
    assert inv.paid_at is not None

    # Invalid: paid -> draft should fail
    with pytest.raises(InvalidStatusTransitionError):
        inv.transition_status(InvoiceStatus.DRAFT)


def test_invoice_line_model(db_session):
    """Verify InvoiceLine model structure and persistence."""
    line = InvoiceLine(
        invoice_id=str(uuid.uuid4()),
        description="Enterprise Subscription Service",
        quantity=Decimal("1.0000"),
        unit_price=Decimal("199.9900"),
        line_total=Decimal("199.9900"),
    )
    assert line.quantity == Decimal("1.0000")
    assert line.unit_price == Decimal("199.9900")

    db_session.add(line)
    db_session.commit()
    assert line.id is not None


def test_payment_model_and_transitions(db_session):
    """Verify Payment lifecycle, transitions, and persistence."""
    pay = Payment(
        invoice_id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        amount=Decimal("199.9900"),
        status=PaymentStatus.RECORDED.value,
    )
    assert pay.status == PaymentStatus.RECORDED.value
    assert pay.reversed_at is None

    db_session.add(pay)
    db_session.commit()
    assert pay.id is not None
    assert pay.currency == "USD"

    # recorded -> reversed
    pay.transition_status(PaymentStatus.REVERSED)
    assert pay.status == PaymentStatus.REVERSED.value
    assert pay.reversed_at is not None

    # Invalid: reversed -> recorded should fail
    with pytest.raises(InvalidStatusTransitionError):
        pay.transition_status(PaymentStatus.RECORDED)


def test_pydantic_schemas():
    """Verify Pydantic schemas validate correctly."""
    # Tax schemas
    tax_in = TaxCreate(name="GST 18%", code="GST-18", rate=Decimal("0.1800"))
    assert tax_in.code == "GST-18"

    tax_out = TaxOut(
        id=str(uuid.uuid4()),
        name=tax_in.name,
        code=tax_in.code,
        rate=tax_in.rate,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert tax_out.rate == Decimal("0.1800")

    # Discount schemas
    disc_in = DiscountCreate(
        code="WELCOME10",
        name="Welcome 10%",
        discount_type=DiscountType.PERCENTAGE,
        value=Decimal("10.0000"),
        product_ids=[str(uuid.uuid4())],
    )
    assert disc_in.value == Decimal("10.0000")

    disc_product_out = DiscountProductOut(
        id=str(uuid.uuid4()),
        discount_id=str(uuid.uuid4()),
        product_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
    )
    assert disc_product_out.id is not None

    disc_app_in = DiscountApplicationCreate(
        discount_id=str(uuid.uuid4()),
        amount_saved=Decimal("15.0000"),
    )
    assert disc_app_in.amount_saved == Decimal("15.0000")

    # Invoice schemas
    line_in = InvoiceLineCreate(
        description="Hosting Plan",
        quantity=Decimal("2.0000"),
        unit_price=Decimal("50.0000"),
    )
    inv_in = InvoiceCreate(
        customer_id=str(uuid.uuid4()),
        due_date=date(2026, 12, 1),
        lines=[line_in],
    )
    assert len(inv_in.lines) == 1

    # Payment schemas
    pay_in = PaymentCreate(
        invoice_id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        amount=Decimal("100.0000"),
        payment_method="stripe",
    )
    assert pay_in.amount == Decimal("100.0000")

    # Password reset schemas
    reset_req = PasswordResetRequest(email="user@brightloop.com")
    assert reset_req.email == "user@brightloop.com"

    reset_conf = PasswordResetConfirm(token="token123", new_password="securepassword123")
    assert len(reset_conf.new_password) >= 8

    # Audit log schema
    log_in = AuditLogCreate(
        action="user.login",
        entity_type="User",
        entity_id=str(uuid.uuid4()),
    )
    assert log_in.action == "user.login"
