"""Prepaid Plans REST API router."""
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.enums import PlanType
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.plan_service import plan_service

router = APIRouter(prefix="/plans", tags=["Prepaid Plans"])


@router.post(
    "/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Prepaid Plan",
    description="Registers a new prepaid plan with validity, data allowance in MB, and pricing. [Protected: Staff/Admin in Phase 5]",
)
def create_plan(
    plan_in: PlanCreate,
    db: Session = Depends(get_db),
) -> PlanResponse:
    return plan_service.create_plan(db=db, plan_in=plan_in)


@router.get(
    "/",
    response_model=PaginatedResponse[PlanResponse],
    summary="List Prepaid Plans",
    description="Lists and filters prepaid plans by price range, validity, daily/bulk data MB, plan type, and circle.",
)
def list_plans(
    search: Optional[str] = Query(None, description="Search by name, code, or description"),
    circle_id: Optional[int] = Query(None, description="Filter by circle ID (includes All-India)"),
    plan_type: Optional[PlanType] = Query(None, description="Filter by plan type"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    min_validity: Optional[int] = Query(None, ge=1, description="Minimum validity days"),
    max_validity: Optional[int] = Query(None, ge=1, description="Maximum validity days"),
    min_data_mb: Optional[int] = Query(None, ge=0, description="Minimum data allowance in MB"),
    max_data_mb: Optional[int] = Query(None, ge=0, description="Maximum data allowance in MB"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlanResponse]:
    return plan_service.list_plans(
        db=db,
        search=search,
        circle_id=circle_id,
        plan_type=plan_type,
        min_price=min_price,
        max_price=max_price,
        min_validity=min_validity,
        max_validity=max_validity,
        min_data_mb=min_data_mb,
        max_data_mb=max_data_mb,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    summary="Get Plan by ID",
    description="Retrieves a specific prepaid plan including computed GB presentation fields.",
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
) -> PlanResponse:
    return plan_service.get_plan(db=db, plan_id=plan_id)


@router.put(
    "/{plan_id}",
    response_model=PlanResponse,
    summary="Update Plan",
    description="Updates prepaid plan details, price, validity, or allowances. [Protected: Staff/Admin in Phase 5]",
)
def update_plan(
    plan_id: int,
    plan_in: PlanUpdate,
    db: Session = Depends(get_db),
) -> PlanResponse:
    return plan_service.update_plan(
        db=db, plan_id=plan_id, plan_in=plan_in
    )


@router.delete(
    "/{plan_id}",
    response_model=MessageResponse,
    summary="Delete or Deactivate Plan",
    description="Safely deactivates plan if active subscribers are enrolled, or deletes it cleanly. [Protected: Admin in Phase 5]",
)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
) -> MessageResponse:
    result = plan_service.delete_or_deactivate_plan(db=db, plan_id=plan_id)
    return MessageResponse(message=result["message"])
