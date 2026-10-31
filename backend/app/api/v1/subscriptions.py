"""
Subscriptions router with status-transition endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.exceptions import InvalidStatusTransitionError
from app.models.subscription import Subscription, SubscriptionLine, SubscriptionStatus
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionStatusUpdate,
    SubscriptionUpdate,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/", response_model=list[SubscriptionOut])
def list_subscriptions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    return db.query(Subscription).offset(skip).limit(limit).all()


@router.post("/", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    sub_data = payload.model_dump(exclude={"lines"})
    subscription = Subscription(**sub_data)
    db.add(subscription)
    db.flush()
    for line_data in payload.lines:
        line = SubscriptionLine(subscription_id=subscription.id, **line_data.model_dump())
        db.add(line)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.get("/{subscription_id}", response_model=SubscriptionOut)
def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")
    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionOut)
def update_subscription(
    subscription_id: str,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subscription, field, value)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.post("/{subscription_id}/status", response_model=SubscriptionOut)
def update_subscription_status(
    subscription_id: str,
    payload: SubscriptionStatusUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    """Apply a validated status transition to a subscription."""
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")
    try:
        subscription.transition_status(payload.status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")
    if subscription.status not in {SubscriptionStatus.DRAFT.value, SubscriptionStatus.CLOSED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or closed subscriptions can be deleted.",
        )
    db.delete(subscription)
    db.commit()
