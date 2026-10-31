"""
Customer service — business logic, RBAC, search, and validation.
"""
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.user import User, UserRole
from app.schemas.customer import CustomerCreate, CustomerUpdate


def get_customer_for_user(db: Session, user: User) -> Customer | None:
    """Retrieve the customer profile associated with a user."""
    return db.query(Customer).filter(Customer.user_id == user.id).first()


def list_customers(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    city: str | None = None,
    country: str | None = None,
) -> list[Customer]:
    """List customers with search, filtering, and role-based isolation."""
    query = db.query(Customer)

    # Customer role can only access their own record
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Customer.user_id == current_user.id)
        return query.all()

    # Search across company name, contact name, and email
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.company_name.ilike(pattern),
                Customer.contact_name.ilike(pattern),
                Customer.email.ilike(pattern),
            )
        )

    if city:
        query = query.filter(Customer.city.ilike(f"%{city.strip()}%"))

    if country:
        query = query.filter(Customer.country == country.strip())

    return query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()


def get_customer(db: Session, current_user: User, customer_id: str) -> Customer:
    """Get a customer by ID with RBAC isolation."""
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    if current_user.role == UserRole.CUSTOMER and customer.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot view other customer profiles.",
        )

    return customer


def create_customer(
    db: Session,
    current_user: User,
    payload: CustomerCreate,
) -> Customer:
    """Create a new customer profile with email uniqueness validation."""
    # Enforce email uniqueness
    existing = db.query(Customer).filter(Customer.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email '{payload.email}' already exists.",
        )

    # If created by customer, auto-assign user_id to themselves
    user_id = payload.user_id
    if current_user.role == UserRole.CUSTOMER:
        user_id = current_user.id

    customer_data = payload.model_dump()
    customer_data["user_id"] = user_id

    customer = Customer(**customer_data)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(
    db: Session,
    current_user: User,
    customer_id: str,
    payload: CustomerUpdate,
) -> Customer:
    """Update customer details with validation and RBAC checks."""
    customer = get_customer(db, current_user, customer_id)

    # If updating email, ensure uniqueness
    update_data = payload.model_dump(exclude_unset=True)
    new_email = update_data.get("email")
    if new_email and new_email != customer.email:
        conflict = (
            db.query(Customer)
            .filter(Customer.email == new_email, Customer.id != customer_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with email '{new_email}' already exists.",
            )

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(
    db: Session,
    current_user: User,
    customer_id: str,
) -> None:
    """Delete a customer. Admin only, prevents deleting if active subscriptions exist."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete customers.",
        )

    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    # Check for linked active subscriptions or invoices
    if customer.subscriptions:
        active_subs = [s for s in customer.subscriptions if s.status not in {"closed", "draft"}]
        if active_subs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete customer with active or confirmed subscriptions.",
            )

    db.delete(customer)
    db.commit()
