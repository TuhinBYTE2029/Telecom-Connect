"""Plan Changes REST API router."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.plan_change import PlanChangeCreate, PlanChangeResponse
from app.schemas.common import PaginatedResponse
from app.services.plan_change_service import plan_change_service

router = APIRouter(prefix="/plan-changes", tags=["Plan Changes"])


@router.post(
    "/",
    response_model=PlanChangeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request Plan Change",
    description="Requests migration of a subscriber to a new prepaid plan. Automatically activates new subscription when status is COMPLETED. [Protected: Staff/Subscriber in Phase 5]",
)
def request_plan_change(
    change_in: PlanChangeCreate,
    db: Session = Depends(get_db),
) -> PlanChangeResponse:
    return plan_change_service.request_plan_change(db=db, change_in=change_in)


@router.get(
    "/record/{change_id}",
    response_model=PlanChangeResponse,
    summary="Get Plan Change Record by ID",
    description="Retrieves a specific plan change audit record including previous and new plan details.",
)
def get_plan_change(
    change_id: int,
    db: Session = Depends(get_db),
) -> PlanChangeResponse:
    return plan_change_service.get_plan_change(db=db, change_id=change_id)


@router.get(
    "/{subscriber_id}",
    response_model=PaginatedResponse[PlanChangeResponse],
    summary="Get Subscriber Plan Change History",
    description="Retrieves complete chronological plan migration history for a subscriber.",
)
def list_subscriber_plan_changes(
    subscriber_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlanChangeResponse]:
    return plan_change_service.list_by_subscriber(
        db=db, subscriber_id=subscriber_id, page=page, page_size=page_size
    )
