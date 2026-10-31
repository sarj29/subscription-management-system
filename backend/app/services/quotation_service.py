"""
Quotation service — business logic, template parsing, line calculations, status transitions, and subscription conversion.
"""
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidStatusTransitionError
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.quotation import Quotation, QuotationLine, QuotationStatus
from app.models.quotation_template import QuotationTemplate
from app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus
from app.models.user import User, UserRole
from app.schemas.quotation import (
    QuotationConvertToSubscription,
    QuotationCreate,
    QuotationLineCreate,
    QuotationUpdate,
)


def compute_quotation_totals(
    lines_data: list[dict[str, Any]],
) -> tuple[Decimal, Decimal, Decimal]:
    """Calculate subtotal, tax_amount, and total_amount from line dictionaries."""
    subtotal = Decimal("0.0000")
    tax_amount = Decimal("0.0000")

    for line in lines_data:
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
    return subtotal, tax_amount, total_amount


def generate_quotation_reference(db: Session) -> str:
    """Generate a unique reference code: QT-YYYYMM-XXXX."""
    prefix = f"QT-{datetime.now(timezone.utc).strftime('%Y%m')}"
    for _ in range(10):
        suffix = uuid.uuid4().hex[:4].upper()
        ref = f"{prefix}-{suffix}"
        if not db.query(Quotation).filter(Quotation.reference == ref).first():
            return ref
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def generate_subscription_reference(db: Session) -> str:
    """Generate a unique reference code: SUB-YYYYMM-XXXX."""
    prefix = f"SUB-{datetime.now(timezone.utc).strftime('%Y%m')}"
    for _ in range(10):
        suffix = uuid.uuid4().hex[:4].upper()
        ref = f"{prefix}-{suffix}"
        if not db.query(Subscription).filter(Subscription.reference == ref).first():
            return ref
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def list_quotations(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    customer_id: str | None = None,
    status_filter: QuotationStatus | None = None,
    search: str | None = None,
) -> list[Quotation]:
    """List quotations with customer isolation and search."""
    query = db.query(Quotation)

    # Customer isolation
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Quotation.customer_id == cust.id)
    elif customer_id:
        query = query.filter(Quotation.customer_id == customer_id)

    if status_filter:
        query = query.filter(Quotation.status == status_filter.value)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Quotation.reference.ilike(pattern),
                Quotation.notes.ilike(pattern),
            )
        )

    return query.order_by(Quotation.created_at.desc()).offset(skip).limit(limit).all()


def get_quotation(db: Session, current_user: User, quotation_id: str) -> Quotation:
    """Retrieve quotation by ID enforcing customer isolation."""
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found.",
        )

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or quotation.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot view other customer quotations.",
            )

    return quotation


def create_quotation(
    db: Session,
    current_user: User,
    payload: QuotationCreate,
) -> Quotation:
    """Create quotation supporting templates, unique reference, and line totals."""
    # Validate customer exists
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    if current_user.role == UserRole.CUSTOMER and customer.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot create quotations for other customer profiles.",
        )

    # Generate reference if absent
    ref = payload.reference or generate_quotation_reference(db)
    if db.query(Quotation).filter(Quotation.reference == ref).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quotation with reference '{ref}' already exists.",
        )

    valid_until = payload.valid_until or (date.today() + timedelta(days=30))
    raw_lines = [l.model_dump() for l in payload.lines]

    # Template fallback if lines empty and template_id supplied
    if not raw_lines and payload.template_id:
        template = db.get(QuotationTemplate, payload.template_id)
        if template and template.body:
            try:
                parsed = json.loads(template.body)
                if isinstance(parsed, list):
                    raw_lines = parsed
            except Exception:
                pass

    subtotal, tax_amount, total_amount = compute_quotation_totals(raw_lines)

    quotation = Quotation(
        customer_id=payload.customer_id,
        template_id=payload.template_id,
        reference=ref,
        status=QuotationStatus.DRAFT.value,
        valid_until=valid_until,
        notes=payload.notes,
        currency=payload.currency,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
    db.add(quotation)
    db.flush()

    for idx, l_data in enumerate(raw_lines):
        line = QuotationLine(
            quotation_id=quotation.id,
            description=l_data.get("description", "Quotation Line Item"),
            quantity=Decimal(str(l_data.get("quantity", "1.0000"))),
            unit_price=Decimal(str(l_data.get("unit_price", "0.0000"))),
            discount_percent=Decimal(str(l_data.get("discount_percent", "0.00"))),
            tax_percent=Decimal(str(l_data.get("tax_percent", "0.00"))),
            line_total=Decimal(str(l_data.get("line_total", "0.0000"))),
            position=l_data.get("position", idx),
            product_variant_id=l_data.get("product_variant_id"),
        )
        db.add(line)

    db.commit()
    db.refresh(quotation)
    return quotation


def update_quotation(
    db: Session,
    current_user: User,
    quotation_id: str,
    payload: QuotationUpdate,
) -> Quotation:
    """Update quotation metadata and optionally replace lines."""
    quotation = get_quotation(db, current_user, quotation_id)

    if quotation.status not in {QuotationStatus.DRAFT.value, QuotationStatus.QUOTATION.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update quotation in '{quotation.status}' status.",
        )

    update_dict = payload.model_dump(exclude_unset=True)

    if "reference" in update_dict and update_dict["reference"] != quotation.reference:
        ref_exists = (
            db.query(Quotation)
            .filter(Quotation.reference == update_dict["reference"], Quotation.id != quotation_id)
            .first()
        )
        if ref_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Quotation with reference '{update_dict['reference']}' already exists.",
            )

    # Handle line updates if provided
    if "lines" in update_dict and update_dict["lines"] is not None:
        raw_lines = update_dict.pop("lines")
        subtotal, tax_amount, total_amount = compute_quotation_totals(raw_lines)
        quotation.subtotal = subtotal
        quotation.tax_amount = tax_amount
        quotation.total_amount = total_amount

        # Replace existing lines
        db.query(QuotationLine).filter(QuotationLine.quotation_id == quotation_id).delete()
        for idx, l_data in enumerate(raw_lines):
            line = QuotationLine(
                quotation_id=quotation.id,
                description=l_data.get("description", "Quotation Line Item"),
                quantity=Decimal(str(l_data.get("quantity", "1.0000"))),
                unit_price=Decimal(str(l_data.get("unit_price", "0.0000"))),
                discount_percent=Decimal(str(l_data.get("discount_percent", "0.00"))),
                tax_percent=Decimal(str(l_data.get("tax_percent", "0.00"))),
                line_total=Decimal(str(l_data.get("line_total", "0.0000"))),
                position=l_data.get("position", idx),
                product_variant_id=l_data.get("product_variant_id"),
            )
            db.add(line)

    for field, val in update_dict.items():
        setattr(quotation, field, val)

    db.commit()
    db.refresh(quotation)
    return quotation


def update_quotation_status(
    db: Session,
    current_user: User,
    quotation_id: str,
    new_status: QuotationStatus,
) -> Quotation:
    """Transition quotation status using domain state machine."""
    quotation = get_quotation(db, current_user, quotation_id)
    try:
        quotation.transition_status(new_status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    db.commit()
    db.refresh(quotation)
    return quotation


def convert_to_subscription(
    db: Session,
    current_user: User,
    quotation_id: str,
    payload: QuotationConvertToSubscription,
) -> Subscription:
    """Convert a confirmed quotation into an active/confirmed subscription."""
    quotation = get_quotation(db, current_user, quotation_id)

    # Quotation must be confirmed
    if quotation.status != QuotationStatus.CONFIRMED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only confirmed quotations can be converted to subscriptions. Current status: '{quotation.status}'.",
        )

    # Check for existing conversion
    existing_sub = (
        db.query(Subscription)
        .filter(Subscription.quotation_id == quotation_id)
        .first()
    )
    if existing_sub:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quotation has already been converted to subscription '{existing_sub.reference or existing_sub.id}'.",
        )

    # Verify plan exists
    plan = db.get(Plan, payload.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target plan not found.",
        )

    sub_ref = generate_subscription_reference(db)
    start = payload.start_date or date.today()

    subscription = Subscription(
        customer_id=quotation.customer_id,
        plan_id=plan.id,
        quotation_id=quotation.id,
        reference=sub_ref,
        status=SubscriptionStatus.CONFIRMED.value,
        start_date=start,
        notes=payload.notes or quotation.notes,
        subtotal=quotation.subtotal,
        tax_amount=quotation.tax_amount,
        total_amount=quotation.total_amount,
        currency=quotation.currency,
    )
    db.add(subscription)
    db.flush()

    # Copy lines
    for line in quotation.lines:
        sub_line = SubscriptionLine(
            subscription_id=subscription.id,
            product_variant_id=line.product_variant_id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent,
            tax_percent=line.tax_percent,
            line_total=line.line_total,
            position=line.position,
        )
        db.add(sub_line)

    db.commit()
    db.refresh(subscription)
    return subscription


def delete_quotation(
    db: Session,
    current_user: User,
    quotation_id: str,
) -> None:
    """Delete draft or cancelled quotation."""
    quotation = get_quotation(db, current_user, quotation_id)
    if quotation.status not in {QuotationStatus.DRAFT.value, QuotationStatus.CANCELLED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or cancelled quotations can be deleted.",
        )
    db.delete(quotation)
    db.commit()
