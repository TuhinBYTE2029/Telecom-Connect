"""API v1 router aggregator."""
from fastapi import APIRouter
from app.api.v1.circles import router as circles_router
from app.api.v1.plans import router as plans_router
from app.api.v1.subscribers import router as subscribers_router
from app.api.v1.recharges import router as recharges_router
from app.api.v1.usage import router as usage_router
from app.api.v1.complaints import router as complaints_router
from app.api.v1.plan_changes import router as plan_changes_router

api_router = APIRouter()
api_router.include_router(circles_router)
api_router.include_router(plans_router)
api_router.include_router(subscribers_router)
api_router.include_router(recharges_router)
api_router.include_router(usage_router)
api_router.include_router(complaints_router)
api_router.include_router(plan_changes_router)
