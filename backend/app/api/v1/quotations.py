"""
Quotations router — CRUD, status transitions, and subscription conversion.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.quotation import QuotationStatus
from app.models.user import User
from app.schemas.quotation import (
    QuotationConvertToSubscription,
    QuotationCreate,
    QuotationOut,
    QuotationStatusUpdate,
    QuotationUpdate,
)
from app.schemas.subscription import SubscriptionOut
from app.services import quotation_service

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.get("/", response_model=list[QuotationOut])
def list_quotations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    status: QuotationStatus | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search reference or notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List quotations with customer isolation and status filter."""
    return quotation_service.list_quotations(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status_filter=status,
        search=search,
    )


@router.post("/", response_model=QuotationOut, status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create quotation with line totals and optional template derivation."""
    return quotation_service.create_quotation(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(
    quotation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get quotation by ID."""
    return quotation_service.get_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
    )


@router.patch("/{quotation_id}", response_model=QuotationOut)
def update_quotation(
    quotation_id: str,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update quotation metadata or lines (draft/quotation only)."""
    return quotation_service.update_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
        payload=payload,
    )


@router.post("/{quotation_id}/status", response_model=QuotationOut)
def update_quotation_status(
    quotation_id: str,
    payload: QuotationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply a validated status transition (draft -> quotation -> confirmed / cancelled)."""
    return quotation_service.update_quotation_status(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
        new_status=payload.status,
    )


@router.post("/{quotation_id}/convert-to-subscription", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def convert_to_subscription(
    quotation_id: str,
    payload: QuotationConvertToSubscription,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Convert a confirmed quotation into an active subscription."""
    return quotation_service.convert_to_subscription(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
        payload=payload,
    )


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quotation(
    quotation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete draft or cancelled quotation."""
    quotation_service.delete_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
    )
