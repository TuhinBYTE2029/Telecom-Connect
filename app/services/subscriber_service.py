"""Subscriber business logic service."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.subscriber import Subscriber
from app.models.enums import SubscriberStatus
from app.schemas.subscriber import (
    SubscriberCreate,
    SubscriberUpdate,
    SubscriberResponse,
    SubscriberDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.repositories.subscriber_repo import subscriber_repo
from app.repositories.circle_repo import circle_repo
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError


class SubscriberService:
    def create_subscriber(
        self, db: Session, sub_in: SubscriberCreate
    ) -> SubscriberResponse:
        """Register new subscriber with uniqueness & relationship validations."""
        # Validate circle exists
        circle = circle_repo.get_by_id(db, sub_in.circle_id)
        if not circle:
            raise NotFoundError(
                f"Telecom circle with ID {sub_in.circle_id} not found"
            )

        # Check mobile uniqueness
        existing_mobile = subscriber_repo.get_by_mobile(db, sub_in.mobile_number)
        if existing_mobile:
            raise ConflictError(
                f"Subscriber with mobile number '{sub_in.mobile_number}' already exists"
            )

        # Check SIM card uniqueness
        existing_sim = subscriber_repo.get_by_sim(db, sub_in.sim_card_number)
        if existing_sim:
            raise ConflictError(
                f"SIM card number '{sub_in.sim_card_number}' is already registered"
            )

        # Ensure initial status for ported_out sets ported_out_at
        now = datetime.now(timezone.utc)
        ported_out_at = now if sub_in.status == SubscriberStatus.PORTED_OUT else None

        subscriber = Subscriber(
            user_id=sub_in.user_id,
            circle_id=sub_in.circle_id,
            mobile_number=sub_in.mobile_number.strip(),
            full_name=sub_in.full_name.strip(),
            email=sub_in.email.strip() if sub_in.email else None,
            status=sub_in.status,
            sim_card_number=sub_in.sim_card_number.strip(),
            activation_date=now,
            ported_out_at=ported_out_at,
        )
        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)
        return SubscriberResponse.model_validate(subscriber)

    def get_subscriber(self, db: Session, sub_id: int) -> SubscriberDetailResponse:
        """Fetch subscriber with circle details by ID."""
        subscriber = subscriber_repo.get_by_id_with_circle(db, sub_id)
        if not subscriber:
            raise NotFoundError(f"Subscriber with ID {sub_id} not found")
        return SubscriberDetailResponse.model_validate(subscriber)

    def get_subscriber_by_mobile(
        self, db: Session, mobile_number: str
    ) -> SubscriberDetailResponse:
        """Fetch subscriber with circle details by mobile number."""
        subscriber = subscriber_repo.get_by_mobile(db, mobile_number)
        if not subscriber:
            raise NotFoundError(
                f"Subscriber with mobile number '{mobile_number}' not found"
            )
        return SubscriberDetailResponse.model_validate(subscriber)

    def list_subscribers(
        self,
        db: Session,
        search: Optional[str] = None,
        status: Optional[SubscriberStatus] = None,
        circle_id: Optional[int] = None,
        exclude_ported_out: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[SubscriberResponse]:
        """List subscribers with search, filters, and pagination."""
        offset = (page - 1) * page_size
        items, total = subscriber_repo.search_and_filter(
            db=db,
            search=search,
            status=status,
            circle_id=circle_id,
            exclude_ported_out=exclude_ported_out,
            offset=offset,
            limit=page_size,
        )
        responses = [SubscriberResponse.model_validate(s) for s in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )

    def update_subscriber(
        self, db: Session, sub_id: int, sub_in: SubscriberUpdate
    ) -> SubscriberResponse:
        """Update subscriber details, enforcing ported-out subscriber integrity."""
        subscriber = subscriber_repo.get_by_id(db, sub_id)
        if not subscriber:
            raise NotFoundError(f"Subscriber with ID {sub_id} not found")

        update_data = sub_in.model_dump(exclude_unset=True)

        if "circle_id" in update_data and update_data["circle_id"] is not None:
            circle = circle_repo.get_by_id(db, update_data["circle_id"])
            if not circle:
                raise NotFoundError(
                    f"Telecom circle with ID {update_data['circle_id']} not found"
                )

        # Enforce business rule: Ported-out subscribers must not remain active / cannot be directly activated
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            if subscriber.status == SubscriberStatus.PORTED_OUT and new_status == SubscriberStatus.ACTIVE:
                raise BadRequestError(
                    "Ported-out subscribers cannot be reactivated directly. Port-in/re-verification required."
                )

            if new_status == SubscriberStatus.PORTED_OUT and subscriber.status != SubscriberStatus.PORTED_OUT:
                subscriber.ported_out_at = datetime.now(timezone.utc)
            elif new_status != SubscriberStatus.PORTED_OUT:
                subscriber.ported_out_at = None

        for field, value in update_data.items():
            if value is not None and isinstance(value, str):
                value = value.strip()
            setattr(subscriber, field, value)

        db.commit()
        db.refresh(subscriber)
        return SubscriberResponse.model_validate(subscriber)

    def delete_subscriber(self, db: Session, sub_id: int) -> dict:
        """Safely delete subscriber record."""
        subscriber = subscriber_repo.get_by_id(db, sub_id)
        if not subscriber:
            raise NotFoundError(f"Subscriber with ID {sub_id} not found")

        mobile = subscriber.mobile_number
        db.delete(subscriber)
        db.commit()
        return {"message": f"Subscriber '{mobile}' deleted successfully."}


subscriber_service = SubscriberService()
