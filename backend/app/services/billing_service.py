"""
Billing service — integration points with invoices, payments, taxes, and discounts.
Provides subscription-to-invoice generation and invoice/payment CRUD operations.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidStatusTransitionError
from app.models.customer import Customer
from app.models.discount import Discount, DiscountType
from app.models.discount_product import DiscountProduct
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import Subscription
from app.models.tax import Tax
from app.models.user import User, UserRole
from app.schemas.discount import DiscountCreate, DiscountUpdate
from app.schemas.invoice import InvoiceCreate, InvoiceStatusUpdate
from app.schemas.payment import PaymentCreate, PaymentStatusUpdate
from app.schemas.tax import TaxCreate, TaxUpdate


def generate_invoice_number(db: Session) -> str:
    """Generate a unique invoice number: INV-YYYYMM-XXXX."""
    prefix = f"INV-{datetime.now(timezone.utc).strftime('%Y%m')}"
    for _ in range(10):
        suffix = uuid.uuid4().hex[:4].upper()
        num = f"{prefix}-{suffix}"
        if not db.query(Invoice).filter(Invoice.invoice_number == num).first():
            return num
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def generate_payment_number(db: Session) -> str:
    """Generate a unique payment number: PAY-YYYYMM-XXXX."""
    prefix = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m')}"
    for _ in range(10):
        suffix = uuid.uuid4().hex[:4].upper()
        num = f"{prefix}-{suffix}"
        if not db.query(Payment).filter(Payment.payment_number == num).first():
            return num
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Subscription-to-Invoice Integration
# ---------------------------------------------------------------------------

def generate_invoice_from_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
    due_days: int = 14,
) -> Invoice:
    """Generate a draft invoice from an active or confirmed subscription."""
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or subscription.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot generate invoices for other customers.",
            )

    inv_num = generate_invoice_number(db)
    today = date.today()
    due = today + timedelta(days=due_days)

    invoice = Invoice(
        invoice_number=inv_num,
        customer_id=subscription.customer_id,
        subscription_id=subscription.id,
        status=InvoiceStatus.DRAFT.value,
        issue_date=today,
        due_date=due,
        subtotal=subscription.subtotal,
        tax_amount=subscription.tax_amount,
        total_amount=subscription.total_amount,
        currency=subscription.currency,
        notes=f"Generated from subscription {subscription.reference or subscription.id}",
    )
    db.add(invoice)
    db.flush()

    for line in subscription.lines:
        inv_line = InvoiceLine(
            invoice_id=invoice.id,
            product_variant_id=line.product_variant_id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent,
            tax_percent=line.tax_percent,
            line_total=line.line_total,
            position=line.position,
        )
        db.add(inv_line)

    db.commit()
    db.refresh(invoice)
    return invoice


# ---------------------------------------------------------------------------
# Invoices CRUD
# ---------------------------------------------------------------------------

def list_invoices(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    customer_id: str | None = None,
    subscription_id: str | None = None,
    status_filter: InvoiceStatus | None = None,
    search: str | None = None,
) -> list[Invoice]:
    """List invoices with customer isolation and status filter."""
    query = db.query(Invoice)

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Invoice.customer_id == cust.id)
    elif customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if subscription_id:
        query = query.filter(Invoice.subscription_id == subscription_id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter.value)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Invoice.invoice_number.ilike(pattern),
                Invoice.notes.ilike(pattern),
            )
        )

    return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()


def get_invoice(db: Session, current_user: User, invoice_id: str) -> Invoice:
    """Get single invoice with customer isolation."""
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or invoice.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot view other customer invoices.",
            )

    return invoice


def create_invoice(
    db: Session,
    current_user: User,
    payload: InvoiceCreate,
) -> Invoice:
    """Create manual invoice."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff or admin can create manual invoices.",
        )

    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    inv_num = payload.invoice_number or generate_invoice_number(db)
    if db.query(Invoice).filter(Invoice.invoice_number == inv_num).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number '{inv_num}' already exists.",
        )

    # Compute lines
    subtotal = Decimal("0.0000")
    tax_amount = Decimal("0.0000")
    raw_lines = [l.model_dump() for l in payload.lines]

    for line in raw_lines:
        qty = Decimal(str(line.get("quantity", "1.0000")))
        price = Decimal(str(line.get("unit_price", "0.0000")))
        disc_pct = Decimal(str(line.get("discount_percent", "0.00")))
        tax_pct = Decimal(str(line.get("tax_percent", "0.00")))

        disc_factor = Decimal("1.0000") - (disc_pct / Decimal("100.00"))
        line_sub = (qty * price * disc_factor).quantize(Decimal("0.0001"))
        line_tax = (line_sub * (tax_pct / Decimal("100.00"))).quantize(Decimal("0.0001"))

        line["line_total"] = line_sub
        subtotal += line_sub
        tax_amount += line_tax

    total_amount = subtotal + tax_amount

    invoice = Invoice(
        invoice_number=inv_num,
        customer_id=payload.customer_id,
        subscription_id=payload.subscription_id,
        status=InvoiceStatus.DRAFT.value,
        issue_date=payload.issue_date or date.today(),
        due_date=payload.due_date,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency=payload.currency,
        notes=payload.notes,
    )
    db.add(invoice)
    db.flush()

    for idx, l_data in enumerate(raw_lines):
        line = InvoiceLine(
            invoice_id=invoice.id,
            product_variant_id=l_data.get("product_variant_id"),
            description=l_data.get("description", "Invoice Item"),
            quantity=Decimal(str(l_data.get("quantity", "1.0000"))),
            unit_price=Decimal(str(l_data.get("unit_price", "0.0000"))),
            discount_percent=Decimal(str(l_data.get("discount_percent", "0.00"))),
            tax_percent=Decimal(str(l_data.get("tax_percent", "0.00"))),
            line_total=Decimal(str(l_data.get("line_total", "0.0000"))),
            position=l_data.get("position", idx),
        )
        db.add(line)

    db.commit()
    db.refresh(invoice)
    return invoice


def update_invoice_status(
    db: Session,
    current_user: User,
    invoice_id: str,
    new_status: InvoiceStatus,
) -> Invoice:
    """Transition invoice status: draft -> confirmed -> paid -> cancelled."""
    invoice = get_invoice(db, current_user, invoice_id)
    try:
        invoice.transition_status(new_status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    db.commit()
    db.refresh(invoice)
    return invoice


# ---------------------------------------------------------------------------
# Payments CRUD
# ---------------------------------------------------------------------------

def list_payments(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    customer_id: str | None = None,
    invoice_id: str | None = None,
    status_filter: PaymentStatus | None = None,
) -> list[Payment]:
    """List payments with customer isolation."""
    query = db.query(Payment)

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Payment.customer_id == cust.id)
    elif customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)

    if status_filter:
        query = query.filter(Payment.status == status_filter.value)

    return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


def get_payment(db: Session, current_user: User, payment_id: str) -> Payment:
    """Get single payment with customer isolation."""
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or payment.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot view other customer payments.",
            )

    return payment


def record_payment(
    db: Session,
    current_user: User,
    payload: PaymentCreate,
) -> Payment:
    """Record a payment against an invoice."""
    invoice = db.get(Invoice, payload.invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or invoice.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot pay invoices for other customers.",
            )

    pay_num = payload.payment_number or generate_payment_number(db)
    payment = Payment(
        invoice_id=payload.invoice_id,
        customer_id=payload.customer_id,
        payment_number=pay_num,
        amount=payload.amount,
        currency=payload.currency,
        payment_method=payload.payment_method,
        transaction_reference=payload.transaction_reference,
        notes=payload.notes,
        status=PaymentStatus.RECORDED.value,
    )
    db.add(payment)

    # Check total payments recorded against this invoice
    total_paid = sum(
        p.amount for p in invoice.payments if p.status == PaymentStatus.RECORDED.value
    ) + payload.amount

    if total_paid >= invoice.total_amount and invoice.status != InvoiceStatus.PAID.value:
        invoice.transition_status(InvoiceStatus.PAID)

    db.commit()
    db.refresh(payment)
    return payment


def update_payment_status(
    db: Session,
    current_user: User,
    payment_id: str,
    new_status: PaymentStatus,
) -> Payment:
    """Reverse a payment."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff or admin can reverse payments.",
        )

    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    try:
        payment.transition_status(new_status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    db.commit()
    db.refresh(payment)
    return payment


# ---------------------------------------------------------------------------
# Taxes CRUD
# ---------------------------------------------------------------------------

def list_taxes(db: Session, skip: int = 0, limit: int = 50, is_active: bool | None = None) -> list[Tax]:
    query = db.query(Tax)
    if is_active is not None:
        query = query.filter(Tax.is_active == is_active)
    return query.order_by(Tax.created_at.desc()).offset(skip).limit(limit).all()


def create_tax(db: Session, current_user: User, payload: TaxCreate) -> Tax:
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")
    if db.query(Tax).filter(Tax.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Tax code '{payload.code}' exists.")
    tax = Tax(**payload.model_dump())
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax


# ---------------------------------------------------------------------------
# Discounts CRUD
# ---------------------------------------------------------------------------

def list_discounts(db: Session, skip: int = 0, limit: int = 50, is_active: bool | None = None) -> list[Discount]:
    query = db.query(Discount)
    if is_active is not None:
        query = query.filter(Discount.is_active == is_active)
    return query.order_by(Discount.created_at.desc()).offset(skip).limit(limit).all()


def create_discount(db: Session, current_user: User, payload: DiscountCreate) -> Discount:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create discount rules.")
    if db.query(Discount).filter(Discount.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Discount code '{payload.code}' exists.")

    disc_data = payload.model_dump(exclude={"product_ids"})
    disc = Discount(**disc_data)
    db.add(disc)
    db.flush()

    for pid in payload.product_ids:
        dp = DiscountProduct(discount_id=disc.id, product_id=pid)
        db.add(dp)

    db.commit()
    db.refresh(disc)
    return disc
