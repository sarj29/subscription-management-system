"""
Taxes router — configure and query tax rates.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.tax import TaxCreate, TaxOut
from app.services import billing_service

router = APIRouter(prefix="/taxes", tags=["Taxes"])


@router.get("/", response_model=list[TaxOut])
def list_taxes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """List configured tax rates."""
    return billing_service.list_taxes(db=db, skip=skip, limit=limit, is_active=is_active)


@router.post("/", response_model=TaxOut, status_code=status.HTTP_201_CREATED)
def create_tax(
    payload: TaxCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new tax rule (Staff/Admin only)."""
    return billing_service.create_tax(db=db, current_user=current_user, payload=payload)
