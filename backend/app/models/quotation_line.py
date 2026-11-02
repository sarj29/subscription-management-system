"""
QuotationLine model — kept as a standalone file for import clarity.
The actual class is defined in quotation.py; this file re-exports it.
"""
from app.models.quotation import QuotationLine  # noqa: F401

__all__ = ["QuotationLine"]
