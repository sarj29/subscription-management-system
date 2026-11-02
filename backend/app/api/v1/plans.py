"""
Plans router — CRUD endpoints with billing interval and plan settings.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.plan import BillingInterval
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate
from app.services import plan_service

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/", response_model=list[PlanOut])
def list_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, description="Search by plan name or description"),
    billing_interval: BillingInterval | None = Query(None, description="Filter by billing interval"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List plans with interval and active filtering."""
    return plan_service.list_plans(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        billing_interval=billing_interval,
        is_active=is_active,
    )


@router.post("/", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new subscription plan (Admin/Staff only)."""
    return plan_service.create_plan(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Get plan details by ID."""
    return plan_service.get_plan(db=db, plan_id=plan_id)


@router.patch("/{plan_id}", response_model=PlanOut)
def update_plan(
    plan_id: str,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update plan details and configuration (Admin/Staff only)."""
    return plan_service.update_plan(
        db=db,
        current_user=current_user,
        plan_id=plan_id,
        payload=payload,
    )


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a plan (Admin only)."""
    plan_service.delete_plan(
        db=db,
        current_user=current_user,
        plan_id=plan_id,
    )
