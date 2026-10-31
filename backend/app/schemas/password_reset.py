"""
Pydantic schemas for password reset workflows.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordResetOut(BaseModel):
    id: str
    user_id: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
