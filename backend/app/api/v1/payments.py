"""
Payments router — record and reverse payments against invoices.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.payment import PaymentStatus
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentOut,
    PaymentStatusUpdate,
)
from app.services import billing_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=list[PaymentOut])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    invoice_id: str | None = Query(None, description="Filter by invoice ID"),
    status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List payments with customer isolation."""
    return billing_service.list_payments(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        invoice_id=invoice_id,
        status_filter=status,
    )


@router.post("/", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a payment against an invoice."""
    return billing_service.record_payment(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get payment details by ID."""
    return billing_service.get_payment(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
    )


@router.post("/{payment_id}/status", response_model=PaymentOut)
def update_payment_status(
    payment_id: str,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply payment status transition (e.g. recorded -> reversed). Staff/Admin only."""
    return billing_service.update_payment_status(
        db=db,
        current_user=current_user,
        payment_id=payment_id,
        new_status=payload.status,
    )
