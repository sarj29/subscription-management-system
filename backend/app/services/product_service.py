"""
Product and ProductVariant service — business logic, price validation, and adjustments.
"""
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User, UserRole
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantUpdate,
)


def list_products(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    is_active: bool | None = None,
) -> list[Product]:
    """List products with search and active status filter."""
    query = db.query(Product)

    # Customers only see active products
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Product.is_active.is_(True))
    elif is_active is not None:
        query = query.filter(Product.is_active == is_active)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.description.ilike(pattern),
            )
        )

    return query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


def get_product(db: Session, product_id: str) -> Product:
    """Retrieve product by ID."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return product


def create_product(
    db: Session,
    current_user: User,
    payload: ProductCreate,
) -> Product:
    """Create a new product with optional initial variants."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can create products.",
        )

    # Check SKU uniqueness if provided
    if payload.sku:
        existing_sku = db.query(Product).filter(Product.sku == payload.sku).first()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{payload.sku}' already exists.",
            )

    product_data = payload.model_dump(exclude={"variants"})
    product = Product(**product_data)
    db.add(product)
    db.flush()

    for variant_data in payload.variants:
        if variant_data.unit_price < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Variant unit price cannot be negative.",
            )
        if variant_data.sku:
            sku_exists = (
                db.query(ProductVariant)
                .filter(ProductVariant.sku == variant_data.sku)
                .first()
            )
            if sku_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Variant with SKU '{variant_data.sku}' already exists.",
                )
        variant = ProductVariant(product_id=product.id, **variant_data.model_dump())
        db.add(variant)

    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    current_user: User,
    product_id: str,
    payload: ProductUpdate,
) -> Product:
    """Update product metadata."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can update products.",
        )

    product = get_product(db, product_id)
    update_data = payload.model_dump(exclude_unset=True)

    new_sku = update_data.get("sku")
    if new_sku and new_sku != product.sku:
        conflict = (
            db.query(Product)
            .filter(Product.sku == new_sku, Product.id != product_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{new_sku}' already exists.",
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(
    db: Session,
    current_user: User,
    product_id: str,
) -> None:
    """Delete a product (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete products.",
        )

    product = get_product(db, product_id)
    db.delete(product)
    db.commit()


def create_variant(
    db: Session,
    current_user: User,
    product_id: str,
    payload: ProductVariantCreate,
) -> ProductVariant:
    """Add a variant to a product."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can add variants.",
        )

    product = get_product(db, product_id)

    if payload.unit_price < Decimal("0.0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Variant unit price cannot be negative.",
        )

    if payload.sku:
        sku_exists = (
            db.query(ProductVariant)
            .filter(ProductVariant.sku == payload.sku)
            .first()
        )
        if sku_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Variant with SKU '{payload.sku}' already exists.",
            )

    variant = ProductVariant(product_id=product.id, **payload.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def update_variant(
    db: Session,
    current_user: User,
    product_id: str,
    variant_id: str,
    payload: ProductVariantUpdate,
) -> ProductVariant:
    """Update a variant's attributes and price."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can update variants.",
        )

    variant = db.get(ProductVariant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found for the specified product.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "unit_price" in update_data and update_data["unit_price"] < Decimal("0.0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Variant unit price cannot be negative.",
        )

    new_sku = update_data.get("sku")
    if new_sku and new_sku != variant.sku:
        conflict = (
            db.query(ProductVariant)
            .filter(ProductVariant.sku == new_sku, ProductVariant.id != variant_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Variant with SKU '{new_sku}' already exists.",
            )

    for field, value in update_data.items():
        setattr(variant, field, value)

    db.commit()
    db.refresh(variant)
    return variant


def adjust_variant_price(
    db: Session,
    current_user: User,
    product_id: str,
    variant_id: str,
    adjustment: Decimal,
) -> ProductVariant:
    """Adjust a variant's price by an incremental amount (e.g. +560.00 for brand option)."""
    if current_user.role not in {UserRole.ADMIN, UserRole.STAFF}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only staff or admin can adjust variant prices.",
        )

    variant = db.get(ProductVariant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found for the specified product.",
        )

    new_price = variant.unit_price + adjustment
    if new_price < Decimal("0.0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resulting variant price cannot be negative.",
        )

    variant.unit_price = new_price
    db.commit()
    db.refresh(variant)
    return variant


def delete_variant(
    db: Session,
    current_user: User,
    product_id: str,
    variant_id: str,
) -> None:
    """Delete a variant (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete variants.",
        )

    variant = db.get(ProductVariant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found for the specified product.",
        )

    db.delete(variant)
    db.commit()
