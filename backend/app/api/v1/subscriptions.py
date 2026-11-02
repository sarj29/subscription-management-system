"""
Subscriptions router — CRUD, lifecycle status transitions, pause, resume, close, renew, and billing generation.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.subscription import SubscriptionStatus
from app.models.user import User
from app.schemas.invoice import InvoiceOut
from app.schemas.subscription import (
    SubscriptionClose,
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionRenewal,
    SubscriptionStatusUpdate,
    SubscriptionUpdate,
)
from app.services import billing_service, subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/", response_model=list[SubscriptionOut])
def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    plan_id: str | None = Query(None, description="Filter by plan ID"),
    status: SubscriptionStatus | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search reference or notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List subscriptions with customer isolation, status filtering, and search."""
    return subscription_service.list_subscriptions(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        plan_id=plan_id,
        status_filter=status,
        search=search,
    )


@router.post("/", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create subscription validating customer, plan rules, dates, and lines."""
    return subscription_service.create_subscription(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{subscription_id}", response_model=SubscriptionOut)
def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get subscription by ID."""
    return subscription_service.get_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
    )


@router.patch("/{subscription_id}", response_model=SubscriptionOut)
def update_subscription(
    subscription_id: str,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update subscription metadata or replace lines."""
    return subscription_service.update_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
        payload=payload,
    )


@router.post("/{subscription_id}/status", response_model=SubscriptionOut)
def update_subscription_status(
    subscription_id: str,
    payload: SubscriptionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply a validated status transition to a subscription."""
    return subscription_service.update_subscription_status(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
        new_status=payload.status,
    )


@router.post("/{subscription_id}/pause", response_model=SubscriptionOut)
def pause_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Pause an active subscription."""
    return subscription_service.pause_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
    )


@router.post("/{subscription_id}/resume", response_model=SubscriptionOut)
def resume_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Resume a paused subscription."""
    return subscription_service.resume_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
    )


@router.post("/{subscription_id}/close", response_model=SubscriptionOut)
def close_subscription(
    subscription_id: str,
    payload: SubscriptionClose | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Close/terminate a subscription."""
    return subscription_service.close_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
        payload=payload,
    )


@router.post("/{subscription_id}/renew", response_model=SubscriptionOut)
def renew_subscription(
    subscription_id: str,
    payload: SubscriptionRenewal | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Renew an active or closed subscription for the next billing cycle."""
    return subscription_service.renew_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
        payload=payload,
    )


@router.post("/{subscription_id}/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def generate_subscription_invoice(
    subscription_id: str,
    due_days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Billing integration: generate a draft invoice from a subscription."""
    return billing_service.generate_invoice_from_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
        due_days=due_days,
    )


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete draft or closed subscription."""
    subscription_service.delete_subscription(
        db=db,
        current_user=current_user,
        subscription_id=subscription_id,
    )
