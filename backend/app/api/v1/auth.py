"""
Authentication router — register, login, token refresh, me.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserStatus
from app.schemas.auth import RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Create a new staff/customer user account."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password flow — returns access + refresh tokens."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )
    return TokenResponse(
        access_token=create_access_token(subject=user.id, extra_claims={"role": user.role}),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token_str: str, db: Session = Depends(get_db)) -> TokenResponse:
    """Issue a new access token using a valid refresh token."""
    try:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token.")
        user_id: str = payload["sub"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
    user = db.get(User, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
    return TokenResponse(
        access_token=create_access_token(subject=user.id, extra_claims={"role": user.role}),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_active_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
