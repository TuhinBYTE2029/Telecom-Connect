"""Data Usage REST API router."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.usage import (
    UsageRecordCreate,
    UsageRecordResponse,
    UsageSummaryResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.usage_service import usage_service

router = APIRouter(prefix="/usage", tags=["Data Usage"])


@router.post(
    "/",
    response_model=UsageRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Data, Voice or SMS Usage",
    description="Records network consumption for a subscriber in MB. Auto-computes GB presentation field.",
)
def record_usage(
    usage_in: UsageRecordCreate,
    db: Session = Depends(get_db),
) -> UsageRecordResponse:
    return usage_service.record_usage(db=db, usage_in=usage_in)


@router.get(
    "/summary/{subscriber_id}",
    response_model=UsageSummaryResponse,
    summary="Get Subscriber Usage Summary",
    description="Returns aggregated total data used (MB and GB), voice minutes, and SMS counts for a subscriber.",
)
def get_usage_summary(
    subscriber_id: int,
    db: Session = Depends(get_db),
) -> UsageSummaryResponse:
    return usage_service.get_summary(db=db, subscriber_id=subscriber_id)


@router.get(
    "/{subscriber_id}",
    response_model=PaginatedResponse[UsageRecordResponse],
    summary="Get Subscriber Usage Records",
    description="Retrieves itemized usage history for a subscriber with date range and usage type filtering.",
)
def get_subscriber_usage(
    subscriber_id: int,
    date_from: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    usage_type: Optional[str] = Query(None, description="Filter by usage type (DATA, VOICE, SMS, MIXED)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UsageRecordResponse]:
    return usage_service.list_usage(
        db=db,
        subscriber_id=subscriber_id,
        date_from=date_from,
        date_to=date_to,
        usage_type=usage_type,
        page=page,
        page_size=page_size,
    )
