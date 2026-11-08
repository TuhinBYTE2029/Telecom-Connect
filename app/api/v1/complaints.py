"""Complaints REST API router."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.enums import ComplaintCategory, ComplaintStatus, ComplaintChannel
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintPatch,
    ComplaintResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.complaint_service import complaint_service

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "/",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Complaint",
    description="Registers a subscriber complaint. Implements cross-channel duplicate detection to prevent duplicate submissions across APP, Call Center, etc.",
)
def create_complaint(
    complaint_in: ComplaintCreate,
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    return complaint_service.create_complaint(db=db, complaint_in=complaint_in)


@router.get(
    "/",
    response_model=PaginatedResponse[ComplaintResponse],
    summary="List Complaints",
    description="Lists complaints with filters for subscriber, category, status (OPEN, IN_PROGRESS, RESOLVED, REJECTED), channel, and date range.",
)
def list_complaints(
    subscriber_id: Optional[int] = Query(None, description="Filter by subscriber ID"),
    category: Optional[ComplaintCategory] = Query(None, description="Filter by complaint category"),
    status: Optional[ComplaintStatus] = Query(None, description="Filter by status"),
    channel: Optional[ComplaintChannel] = Query(None, description="Filter by intake channel"),
    date_from: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ComplaintResponse]:
    return complaint_service.list_complaints(
        db=db,
        subscriber_id=subscriber_id,
        category=category,
        status=status,
        channel=channel,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get Complaint by ID",
    description="Retrieves ticket details, resolution notes, and intake channel for a specific complaint.",
)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    return complaint_service.get_complaint(db=db, complaint_id=complaint_id)


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update Complaint Status and Resolution",
    description="Updates complaint lifecycle status (IN_PROGRESS, RESOLVED, REJECTED), assigns staff, and records resolution notes. [Protected: Staff/Admin in Phase 5]",
)
def patch_complaint(
    complaint_id: int,
    patch_in: ComplaintPatch,
    db: Session = Depends(get_db),
) -> ComplaintResponse:
    return complaint_service.patch_complaint(
        db=db, complaint_id=complaint_id, patch_in=patch_in
    )
