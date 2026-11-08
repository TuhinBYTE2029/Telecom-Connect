"""Recharges REST API router."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.enums import PaymentStatus, PaymentMethod
from app.schemas.recharge import RechargeCreate, RechargeResponse
from app.schemas.common import PaginatedResponse
from app.services.recharge_service import recharge_service

router = APIRouter(tags=["Recharges"])


@router.post(
    "/recharges",
    response_model=RechargeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Recharge",
    description="Processes a prepaid recharge transaction, activates/extends subscriptions on success, and supports payment simulation. [Protected: Staff/Subscriber in Phase 5]",
)
def create_recharge(
    recharge_in: RechargeCreate,
    db: Session = Depends(get_db),
) -> RechargeResponse:
    return recharge_service.create_recharge(db=db, recharge_in=recharge_in)


@router.get(
    "/recharges",
    response_model=PaginatedResponse[RechargeResponse],
    summary="List Recharges",
    description="Lists recharge transactions with filters for subscriber, status, payment method, date range, and pagination.",
)
def list_recharges(
    subscriber_id: Optional[int] = Query(None, description="Filter by subscriber ID"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    date_from: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[RechargeResponse]:
    return recharge_service.list_recharges(
        db=db,
        subscriber_id=subscriber_id,
        payment_status=payment_status,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/recharges/{recharge_id}",
    response_model=RechargeResponse,
    summary="Get Recharge by ID",
    description="Retrieves a specific recharge transaction including plan details.",
)
def get_recharge(
    recharge_id: int,
    db: Session = Depends(get_db),
) -> RechargeResponse:
    return recharge_service.get_recharge(db=db, recharge_id=recharge_id)


@router.get(
    "/subscribers/{subscriber_id}/recharges",
    response_model=PaginatedResponse[RechargeResponse],
    summary="Get Subscriber Recharge History",
    description="Convenience endpoint to fetch all recharge transactions for a specific subscriber.",
)
def get_subscriber_recharges(
    subscriber_id: int,
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[RechargeResponse]:
    return recharge_service.list_recharges(
        db=db,
        subscriber_id=subscriber_id,
        payment_status=payment_status,
        page=page,
        page_size=page_size,
    )
