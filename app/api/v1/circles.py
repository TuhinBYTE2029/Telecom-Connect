"""Telecom Circles REST API router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.circle import CircleCreate, CircleUpdate, CircleResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.circle_service import circle_service

router = APIRouter(prefix="/circles", tags=["Telecom Circles"])


@router.post(
    "/",
    response_model=CircleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Telecom Circle",
    description="Registers a new telecom circle with unique circle code (e.g. 'GJ', 'MH'). [Protected: Staff/Admin in Phase 5]",
)
def create_circle(
    circle_in: CircleCreate,
    db: Session = Depends(get_db),
) -> CircleResponse:
    return circle_service.create_circle(db=db, circle_in=circle_in)


@router.get(
    "/",
    response_model=PaginatedResponse[CircleResponse],
    summary="List Telecom Circles",
    description="Retrieves paginated list of telecom circles with search and filter parameters.",
)
def list_circles(
    search: Optional[str] = Query(None, description="Search by code, name, or state"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CircleResponse]:
    return circle_service.list_circles(
        db=db,
        search=search,
        state=state,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{circle_id}",
    response_model=CircleResponse,
    summary="Get Circle by ID",
    description="Fetches detailed information for a specific telecom circle.",
)
def get_circle(
    circle_id: int,
    db: Session = Depends(get_db),
) -> CircleResponse:
    return circle_service.get_circle(db=db, circle_id=circle_id)


@router.put(
    "/{circle_id}",
    response_model=CircleResponse,
    summary="Update Circle",
    description="Updates circle attributes such as name, state, and active status. [Protected: Staff/Admin in Phase 5]",
)
def update_circle(
    circle_id: int,
    circle_in: CircleUpdate,
    db: Session = Depends(get_db),
) -> CircleResponse:
    return circle_service.update_circle(
        db=db, circle_id=circle_id, circle_in=circle_in
    )


@router.delete(
    "/{circle_id}",
    response_model=MessageResponse,
    summary="Delete Circle",
    description="Safely removes a telecom circle if no subscribers or plans are assigned. [Protected: Admin in Phase 5]",
)
def delete_circle(
    circle_id: int,
    db: Session = Depends(get_db),
) -> MessageResponse:
    circle_service.delete_circle(db=db, circle_id=circle_id)
    return MessageResponse(
        message=f"Telecom circle with ID {circle_id} deleted successfully."
    )
