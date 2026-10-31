"""
Quotations router with status-transition endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.exceptions import InvalidStatusTransitionError
from app.models.quotation import Quotation, QuotationLine, QuotationStatus
from app.schemas.quotation import (
    QuotationCreate,
    QuotationOut,
    QuotationStatusUpdate,
    QuotationUpdate,
)

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.get("/", response_model=list[QuotationOut])
def list_quotations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    return db.query(Quotation).offset(skip).limit(limit).all()


@router.post("/", response_model=QuotationOut, status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    quotation_data = payload.model_dump(exclude={"lines"})
    quotation = Quotation(**quotation_data)
    db.add(quotation)
    db.flush()
    for line_data in payload.lines:
        line = QuotationLine(quotation_id=quotation.id, **line_data.model_dump())
        db.add(line)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(
    quotation_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")
    return quotation


@router.patch("/{quotation_id}", response_model=QuotationOut)
def update_quotation(
    quotation_id: str,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(quotation, field, value)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.post("/{quotation_id}/status", response_model=QuotationOut)
def update_quotation_status(
    quotation_id: str,
    payload: QuotationStatusUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    """Apply a validated status transition to a quotation."""
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")
    try:
        quotation.transition_status(payload.status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    db.commit()
    db.refresh(quotation)
    return quotation


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quotation(
    quotation_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found.")
    if quotation.status not in {QuotationStatus.DRAFT.value, QuotationStatus.CANCELLED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or cancelled quotations can be deleted.",
        )
    db.delete(quotation)
    db.commit()
