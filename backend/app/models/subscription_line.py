"""
SubscriptionLine model — kept as a standalone file for import clarity.
The actual class is defined in subscription.py; this file re-exports it.
"""
from app.models.subscription import SubscriptionLine  # noqa: F401

__all__ = ["SubscriptionLine"]
