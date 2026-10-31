"""
Pydantic schemas for AuditLog records.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None


class AuditLogCreate(AuditLogBase):
    user_id: str | None = None


class AuditLogOut(AuditLogBase):
    id: str
    user_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
