"""
Products and ProductVariants router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantOut,
    ProductVariantUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------

@router.get("/", response_model=list[ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    return db.query(Product).offset(skip).limit(limit).all()


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    product_data = payload.model_dump(exclude={"variants"})
    product = Product(**product_data)
    db.add(product)
    db.flush()  # populate product.id before creating variants
    for variant_data in payload.variants:
        variant = ProductVariant(product_id=product.id, **variant_data.model_dump())
        db.add(variant)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    db.delete(product)
    db.commit()


# --------------------------------------------------------------------------
# Variants (nested under a product)
# --------------------------------------------------------------------------

@router.post("/{product_id}/variants", response_model=ProductVariantOut, status_code=status.HTTP_201_CREATED)
def create_variant(
    product_id: str,
    payload: ProductVariantCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    variant = ProductVariant(product_id=product_id, **payload.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.patch("/{product_id}/variants/{variant_id}", response_model=ProductVariantOut)
def update_variant(
    product_id: str,
    variant_id: str,
    payload: ProductVariantUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    variant = db.get(ProductVariant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    product_id: str,
    variant_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    variant = db.get(ProductVariant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
    db.delete(variant)
    db.commit()
