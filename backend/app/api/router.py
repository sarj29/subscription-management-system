"""
API v1 router — aggregates all domain routers.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.plans import router as plans_router
from app.api.v1.products import router as products_router
from app.api.v1.quotations import router as quotations_router
from app.api.v1.subscriptions import router as subscriptions_router

# Placeholder routers for Phase 2 (billing module)
# from app.api.v1.invoices import router as invoices_router
# from app.api.v1.payments import router as payments_router
# from app.api.v1.discounts import router as discounts_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(customers_router)
api_router.include_router(products_router)
api_router.include_router(plans_router)
api_router.include_router(quotations_router)
api_router.include_router(subscriptions_router)
