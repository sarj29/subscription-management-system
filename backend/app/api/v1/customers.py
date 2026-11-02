"""
Customers router — CRUD endpoints with validation, search, filtering, and RBAC.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=list[CustomerOut])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, description="Search company name, contact, or email"),
    city: str | None = Query(None, description="Filter by city"),
    country: str | None = Query(None, description="Filter by country"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List customers with search, city/country filtering, and pagination."""
    return customer_service.list_customers(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        city=city,
        country=country,
    )


@router.post("/", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new customer profile with uniqueness and data validation."""
    return customer_service.create_customer(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get customer details by ID (enforces customer isolation)."""
    return customer_service.get_customer(
        db=db,
        current_user=current_user,
        customer_id=customer_id,
    )


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Partial update of a customer profile."""
    return customer_service.update_customer(
        db=db,
        current_user=current_user,
        customer_id=customer_id,
        payload=payload,
    )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a customer profile (Admin only)."""
    customer_service.delete_customer(
        db=db,
        current_user=current_user,
        customer_id=customer_id,
    )
