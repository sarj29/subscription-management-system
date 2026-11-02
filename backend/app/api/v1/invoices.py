"""
Invoices router — query and lifecycle endpoints.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.invoice import InvoiceStatus
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceOut,
    InvoiceStatusUpdate,
)
from app.services import billing_service

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/", response_model=list[InvoiceOut])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    subscription_id: str | None = Query(None, description="Filter by subscription ID"),
    status: InvoiceStatus | None = Query(None, description="Filter by invoice status"),
    search: str | None = Query(None, description="Search invoice number or notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List invoices with customer isolation and status filtering."""
    return billing_service.list_invoices(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        subscription_id=subscription_id,
        status_filter=status,
        search=search,
    )


@router.post("/", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a manual invoice (Staff/Admin only)."""
    return billing_service.create_invoice(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get invoice details by ID."""
    return billing_service.get_invoice(
        db=db,
        current_user=current_user,
        invoice_id=invoice_id,
    )


@router.post("/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: str,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transition invoice status: draft -> confirmed -> paid -> cancelled."""
    return billing_service.update_invoice_status(
        db=db,
        current_user=current_user,
        invoice_id=invoice_id,
        new_status=payload.status,
    )
