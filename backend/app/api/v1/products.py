"""
Products and ProductVariants router — CRUD and price adjustments.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantOut,
    ProductVariantUpdate,
    VariantPriceAdjustment,
)
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------

@router.get("/", response_model=list[ProductOut])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, description="Search by name, SKU, or description"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List products with search and active status filter."""
    return product_service.list_products(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new product with optional initial variants (Admin/Staff only)."""
    return product_service.create_product(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Get product details by ID."""
    return product_service.get_product(db=db, product_id=product_id)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update product metadata (Admin/Staff only)."""
    return product_service.update_product(
        db=db,
        current_user=current_user,
        product_id=product_id,
        payload=payload,
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product (Admin only)."""
    product_service.delete_product(
        db=db,
        current_user=current_user,
        product_id=product_id,
    )


# --------------------------------------------------------------------------
# Variants (nested under a product)
# --------------------------------------------------------------------------

@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantOut,
    status_code=status.HTTP_201_CREATED,
)
def create_variant(
    product_id: str,
    payload: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new variant to an existing product."""
    return product_service.create_variant(
        db=db,
        current_user=current_user,
        product_id=product_id,
        payload=payload,
    )


@router.patch("/{product_id}/variants/{variant_id}", response_model=ProductVariantOut)
def update_variant(
    product_id: str,
    variant_id: str,
    payload: ProductVariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update variant details and pricing."""
    return product_service.update_variant(
        db=db,
        current_user=current_user,
        product_id=product_id,
        variant_id=variant_id,
        payload=payload,
    )


@router.post("/{product_id}/variants/{variant_id}/adjust-price", response_model=ProductVariantOut)
def adjust_variant_price(
    product_id: str,
    variant_id: str,
    payload: VariantPriceAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply an incremental price adjustment to a variant (e.g. +560.00 for Odoo brand)."""
    return product_service.adjust_variant_price(
        db=db,
        current_user=current_user,
        product_id=product_id,
        variant_id=variant_id,
        adjustment=payload.adjustment,
    )


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    product_id: str,
    variant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product variant (Admin only)."""
    product_service.delete_variant(
        db=db,
        current_user=current_user,
        product_id=product_id,
        variant_id=variant_id,
    )
