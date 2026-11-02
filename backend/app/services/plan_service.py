"""
Plan service — business logic, interval validation, availability rules, and settings serialization.
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.plan import BillingInterval, Plan
from app.models.user import User, UserRole
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate


def serialize_settings(
    text: str | None,
    min_quantity: int = 1,
    available_from: datetime | None = None,
    available_until: datetime | None = None,
    auto_close: bool = False,
    allow_pause: bool = True,
    allow_early_closure: bool = True,
    allow_renewal: bool = True,
) -> str:
    """Store plan description and extended business configuration."""
    data = {
        "text": text or "",
        "min_quantity": min_quantity,
        "available_from": available_from.isoformat() if available_from else None,
        "available_until": available_until.isoformat() if available_until else None,
        "auto_close": auto_close,
        "allow_pause": allow_pause,
        "allow_early_closure": allow_early_closure,
        "allow_renewal": allow_renewal,
    }
    return json.dumps(data)


def parse_settings(raw: str | None) -> dict[str, Any]:
    """Extract settings and original description."""
    defaults = {
        "description": raw,
        "min_quantity": 1,
        "available_from": None,
        "available_until": None,
        "auto_close": False,
        "allow_pause": True,
        "allow_early_closure": True,
        "allow_renewal": True,
    }
    if not raw:
        return defaults
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "min_quantity" in data:
            return {
                "description": data.get("text") or None,
                "min_quantity": data.get("min_quantity", 1),
                "available_from": (
                    datetime.fromisoformat(data["available_from"])
                    if data.get("available_from")
                    else None
                ),
                "available_until": (
                    datetime.fromisoformat(data["available_until"])
                    if data.get("available_until")
                    else None
                ),
                "auto_close": data.get("auto_close", False),
                "allow_pause": data.get("allow_pause", True),
                "allow_early_closure": data.get("allow_early_closure", True),
                "allow_renewal": data.get("allow_renewal", True),
            }
    except Exception:
        pass
    return defaults


def plan_to_out(plan: Plan) -> PlanOut:
    """Convert a Plan ORM instance into PlanOut with unpacked settings."""
    settings = parse_settings(plan.description)
    return PlanOut(
        id=plan.id,
        name=plan.name,
        description=settings["description"],
        billing_interval=BillingInterval(plan.billing_interval),
        interval_count=plan.interval_count,
        base_price=plan.base_price,
        currency=plan.currency,
        trial_days=plan.trial_days,
        is_active=plan.is_active,
        min_quantity=settings["min_quantity"],
        available_from=settings["available_from"],
        available_until=settings["available_until"],
        auto_close=settings["auto_close"],
        allow_pause=settings["allow_pause"],
        allow_early_closure=settings["allow_early_closure"],
        allow_renewal=settings["allow_renewal"],
    )


def list_plans(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    billing_interval: BillingInterval | None = None,
    is_active: bool | None = None,
) -> list[PlanOut]:
    """List plans with interval and active status filters."""
    query = db.query(Plan)

    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Plan.is_active.is_(True))
    elif is_active is not None:
        query = query.filter(Plan.is_active == is_active)

    if billing_interval:
        query = query.filter(Plan.billing_interval == billing_interval.value)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Plan.name.ilike(pattern),
                Plan.description.ilike(pattern),
            )
        )

    plans = query.order_by(Plan.created_at.desc()).offset(skip).limit(limit).all()
    return [plan_to_out(p) for p in plans]


def get_plan(db: Session, plan_id: str) -> PlanOut:
    """Get single plan by ID."""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found.",
        )
    return plan_to_out(plan)


def get_plan_model(db: Session, plan_id: str) -> Plan:
    """Internal helper to get raw Plan ORM model."""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found.",
        )
    return plan


def create_plan(
    db: Session,
    current_user: User,
    payload: PlanCreate,
) -> PlanOut:
    """Create a new plan with validated billing interval and settings."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can create plans.",
        )

    if payload.base_price < Decimal("0.0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Plan base price cannot be negative.",
        )

    if payload.available_from and payload.available_until:
        if payload.available_until < payload.available_from:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="available_until cannot be earlier than available_from.",
            )

    serialized_desc = serialize_settings(
        text=payload.description,
        min_quantity=payload.min_quantity,
        available_from=payload.available_from,
        available_until=payload.available_until,
        auto_close=payload.auto_close,
        allow_pause=payload.allow_pause,
        allow_early_closure=payload.allow_early_closure,
        allow_renewal=payload.allow_renewal,
    )

    plan = Plan(
        name=payload.name,
        description=serialized_desc,
        billing_interval=payload.billing_interval.value,
        interval_count=payload.interval_count,
        base_price=payload.base_price,
        currency=payload.currency,
        trial_days=payload.trial_days,
        is_active=payload.is_active,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan_to_out(plan)


def update_plan(
    db: Session,
    current_user: User,
    plan_id: str,
    payload: PlanUpdate,
) -> PlanOut:
    """Update plan attributes and business settings."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can update plans.",
        )

    plan = get_plan_model(db, plan_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "base_price" in update_data and update_data["base_price"] < Decimal("0.0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Plan base price cannot be negative.",
        )

    # Current settings
    curr_settings = parse_settings(plan.description)

    # Check date logic if dates are modified
    from_date = update_data.get("available_from", curr_settings["available_from"])
    until_date = update_data.get("available_until", curr_settings["available_until"])
    if from_date and until_date and until_date < from_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="available_until cannot be earlier than available_from.",
        )

    # Merge settings
    text = update_data.get("description", curr_settings["description"])
    min_quantity = update_data.get("min_quantity", curr_settings["min_quantity"])
    auto_close = update_data.get("auto_close", curr_settings["auto_close"])
    allow_pause = update_data.get("allow_pause", curr_settings["allow_pause"])
    allow_early_closure = update_data.get("allow_early_closure", curr_settings["allow_early_closure"])
    allow_renewal = update_data.get("allow_renewal", curr_settings["allow_renewal"])

    serialized_desc = serialize_settings(
        text=text,
        min_quantity=min_quantity,
        available_from=from_date,
        available_until=until_date,
        auto_close=auto_close,
        allow_pause=allow_pause,
        allow_early_closure=allow_early_closure,
        allow_renewal=allow_renewal,
    )
    plan.description = serialized_desc

    # Update direct plan fields
    for field in ["name", "billing_interval", "interval_count", "base_price", "currency", "trial_days", "is_active"]:
        if field in update_data:
            val = update_data[field]
            if field == "billing_interval" and isinstance(val, BillingInterval):
                val = val.value
            setattr(plan, field, val)

    db.commit()
    db.refresh(plan)
    return plan_to_out(plan)


def delete_plan(
    db: Session,
    current_user: User,
    plan_id: str,
) -> None:
    """Delete a plan (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete plans.",
        )

    plan = get_plan_model(db, plan_id)
    if plan.subscriptions:
        active = [s for s in plan.subscriptions if s.status not in {"closed", "draft"}]
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete plan with active subscriptions.",
            )

    db.delete(plan)
    db.commit()
