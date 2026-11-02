"""
FastAPI dependency functions for authentication and role-based access control.

Usage in route handlers:
    current_user: User = Depends(get_current_active_user)
    admin:        User = Depends(require_role("admin"))
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_access_token

# Lazily imported to avoid circular imports at module level
# (models import Base from database, security imports settings from config)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """Decode the Bearer token and return the matching User row.

    Raises HTTP 401 if the token is missing, expired, or invalid.
    Raises HTTP 404 if the user no longer exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")  # type: ignore[assignment]
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Import here to avoid circular dependency at module load time
    from app.models.user import User  # noqa: PLC0415

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def get_current_active_user(
    current_user: Annotated[object, Depends(get_current_user)],
):
    """Extend get_current_user to reject inactive accounts."""
    from app.models.user import UserStatus  # noqa: PLC0415

    if current_user.status != UserStatus.ACTIVE:  # type: ignore[union-attr]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )
    return current_user


def require_role(*roles: str):
    """Return a FastAPI dependency that allows only users with the given role(s).

    Example:
        @router.delete("/{id}", dependencies=[Depends(require_role("admin"))])
    """

    def _check_role(
        current_user: Annotated[object, Depends(get_current_active_user)],
    ):
        if current_user.role not in roles:  # type: ignore[union-attr]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {' or '.join(roles)}.",
            )
        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Convenience type aliases for cleaner route signatures
# ---------------------------------------------------------------------------
CurrentUser = Annotated[object, Depends(get_current_active_user)]
AdminUser = Annotated[object, Depends(require_role("admin"))]
