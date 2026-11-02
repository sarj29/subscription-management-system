"""
Subscription service — business logic, unique reference generation, billing date calculations, lifecycle state machine, pause, resume, close, and renewal.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidStatusTransitionError
from app.models.customer import Customer
from app.models.plan import BillingInterval, Plan
from app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus
from app.models.user import User, UserRole
from app.schemas.subscription import (
    SubscriptionClose,
    SubscriptionCreate,
    SubscriptionRenewal,
    SubscriptionUpdate,
)
from app.services.plan_service import parse_settings


def calculate_next_billing_date(start: date, interval: str, count: int = 1) -> date:
    """Compute the next billing date based on interval and count."""
    interval_enum = BillingInterval(interval)
    if interval_enum == BillingInterval.DAILY:
        return start + timedelta(days=count)
    elif interval_enum == BillingInterval.WEEKLY:
        return start + timedelta(weeks=count)
    elif interval_enum == BillingInterval.MONTHLY:
        # Approximate month forward by 30 days * count or calendar month
        month = start.month - 1 + count
        year = start.year + month // 12
        new_month = month % 12 + 1
        day = min(start.day, 28)
        return date(year, new_month, day)
    elif interval_enum == BillingInterval.QUARTERLY:
        month = start.month - 1 + (count * 3)
        year = start.year + month // 12
        new_month = month % 12 + 1
        day = min(start.day, 28)
        return date(year, new_month, day)
    elif interval_enum == BillingInterval.YEARLY:
        return date(start.year + count, start.month, min(start.day, 28))
    return start + timedelta(days=30 * count)


def generate_subscription_reference(db: Session) -> str:
    """Generate a unique reference code: SUB-YYYYMM-XXXX."""
    prefix = f"SUB-{datetime.now(timezone.utc).strftime('%Y%m')}"
    for _ in range(10):
        suffix = uuid.uuid4().hex[:4].upper()
        ref = f"{prefix}-{suffix}"
        if not db.query(Subscription).filter(Subscription.reference == ref).first():
            return ref
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def compute_subscription_totals(
    lines_data: list[dict[str, Any]],
) -> tuple[Decimal, Decimal, Decimal]:
    """Calculate subtotal, tax_amount, and total_amount from subscription lines."""
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


def list_subscriptions(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    customer_id: str | None = None,
    plan_id: str | None = None,
    status_filter: SubscriptionStatus | None = None,
    search: str | None = None,
) -> list[Subscription]:
    """List subscriptions with customer isolation, status filtering, and search."""
    query = db.query(Subscription)

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Subscription.customer_id == cust.id)
    elif customer_id:
        query = query.filter(Subscription.customer_id == customer_id)

    if plan_id:
        query = query.filter(Subscription.plan_id == plan_id)

    if status_filter:
        query = query.filter(Subscription.status == status_filter.value)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Subscription.reference.ilike(pattern),
                Subscription.notes.ilike(pattern),
            )
        )

    return query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()


def get_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
) -> Subscription:
    """Get single subscription by ID enforcing customer isolation."""
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
                detail="Access forbidden: cannot view other customer subscriptions.",
            )

    return subscription


def create_subscription(
    db: Session,
    current_user: User,
    payload: SubscriptionCreate,
) -> Subscription:
    """Create subscription validating plan rules, minimum quantities, and dates."""
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    if current_user.role == UserRole.CUSTOMER and customer.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot create subscriptions for other customer profiles.",
        )

    plan = db.get(Plan, payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or inactive.",
        )

    plan_settings = parse_settings(plan.description)
    start = payload.start_date or date.today()

    # Validate plan availability dates
    if plan_settings["available_from"] and start < plan_settings["available_from"].date():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Plan is not available until {plan_settings['available_from'].date()}.",
        )
    if plan_settings["available_until"] and start > plan_settings["available_until"].date():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Plan availability expired on {plan_settings['available_until'].date()}.",
        )

    raw_lines = [l.model_dump() for l in payload.lines]

    # Validate minimum quantity
    total_qty = sum(Decimal(str(l.get("quantity", "1.0000"))) for l in raw_lines)
    min_qty = plan_settings.get("min_quantity", 1)
    if total_qty < Decimal(str(min_qty)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Plan requires a minimum total quantity of {min_qty}. Current total: {total_qty}.",
        )

    # Calculate totals
    subtotal, tax_amount, total_amount = compute_subscription_totals(raw_lines)

    # Reference
    ref = payload.reference or generate_subscription_reference(db)
    if db.query(Subscription).filter(Subscription.reference == ref).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subscription with reference '{ref}' already exists.",
        )

    # Trial and Next Billing Dates
    trial_end = None
    if plan.trial_days > 0:
        trial_end = start + timedelta(days=plan.trial_days)

    billing_start = trial_end if trial_end else start
    next_billing = calculate_next_billing_date(
        billing_start,
        plan.billing_interval,
        plan.interval_count,
    )

    subscription = Subscription(
        customer_id=payload.customer_id,
        plan_id=payload.plan_id,
        quotation_id=payload.quotation_id,
        reference=ref,
        status=SubscriptionStatus.DRAFT.value,
        start_date=start,
        end_date=payload.end_date,
        trial_end_date=trial_end,
        next_billing_date=next_billing,
        notes=payload.notes,
        currency=payload.currency,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
    db.add(subscription)
    db.flush()

    for idx, l_data in enumerate(raw_lines):
        line = SubscriptionLine(
            subscription_id=subscription.id,
            description=l_data.get("description", "Subscription Line Item"),
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
    db.refresh(subscription)
    return subscription


def update_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
    payload: SubscriptionUpdate,
) -> Subscription:
    """Update subscription metadata or lines."""
    subscription = get_subscription(db, current_user, subscription_id)

    if current_user.role == UserRole.CUSTOMER and subscription.status != SubscriptionStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers can only edit subscriptions in draft status.",
        )

    update_dict = payload.model_dump(exclude_unset=True)

    if "reference" in update_dict and update_dict["reference"] != subscription.reference:
        ref_exists = (
            db.query(Subscription)
            .filter(Subscription.reference == update_dict["reference"], Subscription.id != subscription_id)
            .first()
        )
        if ref_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subscription with reference '{update_dict['reference']}' already exists.",
            )

    if "lines" in update_dict and update_dict["lines"] is not None:
        raw_lines = update_dict.pop("lines")
        subtotal, tax_amount, total_amount = compute_subscription_totals(raw_lines)
        subscription.subtotal = subtotal
        subscription.tax_amount = tax_amount
        subscription.total_amount = total_amount

        db.query(SubscriptionLine).filter(SubscriptionLine.subscription_id == subscription_id).delete()
        for idx, l_data in enumerate(raw_lines):
            line = SubscriptionLine(
                subscription_id=subscription.id,
                description=l_data.get("description", "Subscription Line Item"),
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
        setattr(subscription, field, val)

    db.commit()
    db.refresh(subscription)
    return subscription


def update_subscription_status(
    db: Session,
    current_user: User,
    subscription_id: str,
    new_status: SubscriptionStatus,
) -> Subscription:
    """Transition status using domain transition validation."""
    subscription = get_subscription(db, current_user, subscription_id)
    try:
        subscription.transition_status(new_status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    db.commit()
    db.refresh(subscription)
    return subscription


def pause_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
) -> Subscription:
    """Pause an active subscription."""
    subscription = get_subscription(db, current_user, subscription_id)
    if subscription.status != SubscriptionStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot pause subscription in '{subscription.status}' status (must be active).",
        )

    # Check plan allow_pause rule
    plan_settings = parse_settings(subscription.plan.description)
    if not plan_settings.get("allow_pause", True):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The plan for this subscription does not permit pausing.",
        )

    subscription.transition_status(SubscriptionStatus.PAUSED)
    db.commit()
    db.refresh(subscription)
    return subscription


def resume_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
) -> Subscription:
    """Resume a paused subscription."""
    subscription = get_subscription(db, current_user, subscription_id)
    if subscription.status != SubscriptionStatus.PAUSED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot resume subscription in '{subscription.status}' status (must be paused).",
        )

    subscription.transition_status(SubscriptionStatus.ACTIVE)
    db.commit()
    db.refresh(subscription)
    return subscription


def close_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
    payload: SubscriptionClose | None = None,
) -> Subscription:
    """Close/terminate a subscription (early or scheduled)."""
    subscription = get_subscription(db, current_user, subscription_id)
    if subscription.status == SubscriptionStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subscription is already closed.",
        )

    # Check early closure permission if closed before end_date
    today = date.today()
    if subscription.end_date and today < subscription.end_date:
        plan_settings = parse_settings(subscription.plan.description)
        if not plan_settings.get("allow_early_closure", True) and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This plan does not permit early closure before its scheduled end date.",
            )

    close_date = payload.close_date if payload and payload.close_date else today
    subscription.end_date = close_date
    if payload and payload.reason:
        existing_notes = subscription.notes or ""
        subscription.notes = f"{existing_notes}\n[Closed: {payload.reason}]".strip()

    subscription.transition_status(SubscriptionStatus.CLOSED)
    db.commit()
    db.refresh(subscription)
    return subscription


def renew_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
    payload: SubscriptionRenewal | None = None,
) -> Subscription:
    """Renew an active or closed subscription; extends billing cycles and prevents duplicates."""
    subscription = get_subscription(db, current_user, subscription_id)

    plan_settings = parse_settings(subscription.plan.description)
    if not plan_settings.get("allow_renewal", True):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This plan does not permit subscription renewal.",
        )

    if subscription.status not in {SubscriptionStatus.ACTIVE.value, SubscriptionStatus.CLOSED.value, SubscriptionStatus.CONFIRMED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot renew subscription in '{subscription.status}' status.",
        )

    today = date.today()
    base_start = payload.start_date if payload and payload.start_date else (subscription.end_date or today)
    if base_start < today:
        base_start = today

    # Calculate next period
    new_next_billing = calculate_next_billing_date(
        base_start,
        subscription.plan.billing_interval,
        subscription.plan.interval_count,
    )

    subscription.start_date = base_start
    subscription.next_billing_date = new_next_billing
    subscription.status = SubscriptionStatus.ACTIVE.value

    if payload and payload.notes:
        existing_notes = subscription.notes or ""
        subscription.notes = f"{existing_notes}\n[Renewed: {payload.notes}]".strip()

    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(
    db: Session,
    current_user: User,
    subscription_id: str,
) -> None:
    """Delete draft or closed subscription."""
    subscription = get_subscription(db, current_user, subscription_id)
    if subscription.status not in {SubscriptionStatus.DRAFT.value, SubscriptionStatus.CLOSED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or closed subscriptions can be deleted.",
        )
    db.delete(subscription)
    db.commit()
