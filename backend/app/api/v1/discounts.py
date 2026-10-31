"""
Discounts router — configure and query discounts and promotion rules.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.discount import DiscountCreate, DiscountOut
from app.services import billing_service

router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.get("/", response_model=list[DiscountOut])
def list_discounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """List discount codes and rules."""
    return billing_service.list_discounts(db=db, skip=skip, limit=limit, is_active=is_active)


@router.post("/", response_model=DiscountOut, status_code=status.HTTP_201_CREATED)
def create_discount(
    payload: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a discount rule (Admin only)."""
    return billing_service.create_discount(db=db, current_user=current_user, payload=payload)
