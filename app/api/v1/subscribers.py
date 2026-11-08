"""Subscribers REST API router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.enums import SubscriberStatus
from app.schemas.subscriber import (
    SubscriberCreate,
    SubscriberUpdate,
    SubscriberResponse,
    SubscriberDetailResponse,
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.subscriber_service import subscriber_service

router = APIRouter(prefix="/subscribers", tags=["Subscribers"])


@router.post(
    "/",
    response_model=SubscriberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Subscriber",
    description="Registers a new prepaid subscriber with unique mobile number and SIM. [Protected: Staff/Admin in Phase 5]",
)
def create_subscriber(
    sub_in: SubscriberCreate,
    db: Session = Depends(get_db),
) -> SubscriberResponse:
    return subscriber_service.create_subscriber(db=db, sub_in=sub_in)


@router.get(
    "/",
    response_model=PaginatedResponse[SubscriberResponse],
    summary="List Subscribers",
    description="Lists subscribers with search (name, mobile, email, SIM), status filter, circle filter, and pagination.",
)
def list_subscribers(
    search: Optional[str] = Query(None, description="Search by name, mobile, email, SIM"),
    status: Optional[SubscriberStatus] = Query(None, description="Filter by status (active, suspended, ported_out)"),
    circle_id: Optional[int] = Query(None, description="Filter by telecom circle ID"),
    exclude_ported_out: bool = Query(False, description="Exclude ported-out subscribers from result"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SubscriberResponse]:
    return subscriber_service.list_subscribers(
        db=db,
        search=search,
        status=status,
        circle_id=circle_id,
        exclude_ported_out=exclude_ported_out,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/by-mobile/{mobile_number}",
    response_model=SubscriberDetailResponse,
    summary="Get Subscriber by Mobile Number",
    description="Quick lookup of subscriber details and assigned circle by 10-digit mobile number.",
)
def get_subscriber_by_mobile(
    mobile_number: str,
    db: Session = Depends(get_db),
) -> SubscriberDetailResponse:
    return subscriber_service.get_subscriber_by_mobile(
        db=db, mobile_number=mobile_number
    )


@router.get(
    "/{subscriber_id}",
    response_model=SubscriberDetailResponse,
    summary="Get Subscriber by ID",
    description="Retrieves subscriber details including circle metadata.",
)
def get_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
) -> SubscriberDetailResponse:
    return subscriber_service.get_subscriber(db=db, sub_id=subscriber_id)


@router.put(
    "/{subscriber_id}",
    response_model=SubscriberResponse,
    summary="Update Subscriber",
    description="Updates subscriber profile or status. Enforces ported-out validation rule. [Protected: Staff/Admin in Phase 5]",
)
def update_subscriber(
    subscriber_id: int,
    sub_in: SubscriberUpdate,
    db: Session = Depends(get_db),
) -> SubscriberResponse:
    return subscriber_service.update_subscriber(
        db=db, sub_id=subscriber_id, sub_in=sub_in
    )


@router.delete(
    "/{subscriber_id}",
    response_model=MessageResponse,
    summary="Delete Subscriber",
    description="Deletes or de-registers a subscriber record. [Protected: Admin in Phase 5]",
)
def delete_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
) -> MessageResponse:
    result = subscriber_service.delete_subscriber(db=db, sub_id=subscriber_id)
    return MessageResponse(message=result["message"])
