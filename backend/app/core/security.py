"""
Security utilities: password hashing (Argon2 via pwdlib) and JWT tokens (PyJWT).
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing — Argon2
# ---------------------------------------------------------------------------
_password_hash = PasswordHash([Argon2Hasher()])


def hash_password(plain_password: str) -> str:
    """Return the Argon2 hash of *plain_password*."""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    return _password_hash.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------
def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Low-level helper that encodes a JWT."""
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived access JWT for *subject* (typically the user UUID)."""
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims=extra_claims,
    )


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh JWT for *subject*."""
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify *token*.

    Raises:
        jwt.ExpiredSignatureError  – token has expired.
        jwt.InvalidTokenError      – token is invalid for any other reason.
    """
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


def verify_access_token(token: str) -> dict[str, Any]:
    """Decode *token* and assert it is an access token.

    Raises:
        jwt.InvalidTokenError if the token type is not 'access'.
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise InvalidTokenError("Token is not an access token.")
    return payload
