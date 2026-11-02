"""
Staff management router — list and create internal staff users (Admin only).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import RegisterRequest, UserOut

router = APIRouter(prefix="/staff", tags=["Staff Management"])


@router.get("/", response_model=list[UserOut])
def list_staff(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List internal staff members (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list staff.",
        )
    return (
        db.query(User)
        .filter(User.role.in_([UserRole.ADMIN, UserRole.STAFF]))
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: RegisterRequest,
    role: str = Query("staff", pattern="^(staff|admin)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new member of staff (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can add a new member of staff.",
        )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists.",
        )

    user_role = UserRole.ADMIN if role == "admin" else UserRole.STAFF
    staff_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=user_role.value,
        status=UserStatus.ACTIVE.value,
    )
    db.add(staff_user)
    db.commit()
    db.refresh(staff_user)
    return staff_user
