"""
InvoiceLine model — kept as a standalone file for import clarity.
The actual class is defined in invoice.py; this file re-exports it.
"""
from app.models.invoice import InvoiceLine  # noqa: F401

__all__ = ["InvoiceLine"]
