"""PlanChange business logic service."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.plan_change import PlanChange
from app.models.subscription import Subscription
from app.models.enums import SubscriberStatus, PlanChangeStatus
from app.schemas.plan_change import PlanChangeCreate, PlanChangeResponse
from app.schemas.common import PaginatedResponse
from app.repositories.plan_change_repo import plan_change_repo
from app.repositories.subscriber_repo import subscriber_repo
from app.repositories.plan_repo import plan_repo
from app.repositories.recharge_repo import recharge_repo
from app.core.exceptions import NotFoundError, BadRequestError, ConflictError


class PlanChangeService:
    def request_plan_change(
        self, db: Session, change_in: PlanChangeCreate
    ) -> PlanChangeResponse:
        """Process plan change request, updating active subscriptions upon completion."""
        # 1. Validate subscriber
        subscriber = subscriber_repo.get_by_id(db, change_in.subscriber_id)
        if not subscriber:
            raise NotFoundError(
                f"Subscriber with ID {change_in.subscriber_id} not found"
            )
        if subscriber.status == SubscriberStatus.PORTED_OUT:
            raise BadRequestError("Ported-out subscribers cannot change plans")

        # 2. Validate target plan
        new_plan = plan_repo.get_by_id(db, change_in.new_plan_id)
        if not new_plan:
            raise NotFoundError(f"Plan with ID {change_in.new_plan_id} not found")
        if not new_plan.is_active:
            raise BadRequestError(f"Target plan '{new_plan.code}' is inactive")

        # 3. Check current subscription
        current_sub = recharge_repo.get_active_subscription(db, subscriber.id)
        old_plan_id = current_sub.plan_id if current_sub else None

        if old_plan_id == new_plan.id:
            raise BadRequestError(
                f"Subscriber is already actively enrolled in plan '{new_plan.code}'"
            )

        # 4. Check for duplicate pending requests
        status = change_in.status or PlanChangeStatus.COMPLETED
        if (
            status == PlanChangeStatus.PENDING
            and plan_change_repo.has_pending_change(db, subscriber.id, new_plan.id)
        ):
            raise ConflictError(
                f"A plan change request to '{new_plan.code}' is already pending for this subscriber"
            )

        now = datetime.now(timezone.utc)
        plan_change = PlanChange(
            subscriber_id=subscriber.id,
            old_plan_id=old_plan_id,
            new_plan_id=new_plan.id,
            status=status,
            reason=change_in.reason.strip() if change_in.reason else None,
            changed_by_user_id=change_in.changed_by_user_id,
            effective_date=now,
        )
        db.add(plan_change)

        # 5. Update active subscriptions only when change is COMPLETED
        if status == PlanChangeStatus.COMPLETED:
            if current_sub:
                current_sub.is_active = False
            new_sub = Subscription(
                subscriber_id=subscriber.id,
                plan_id=new_plan.id,
                start_date=now,
                end_date=now + timedelta(days=new_plan.validity_days),
                is_active=True,
                auto_renew=False,
            )
            db.add(new_sub)

        db.commit()
        db.refresh(plan_change)
        return PlanChangeResponse.model_validate(plan_change)

    def get_plan_change(self, db: Session, change_id: int) -> PlanChangeResponse:
        """Fetch plan change record by ID."""
        record = plan_change_repo.get_by_id_with_plans(db, change_id)
        if not record:
            raise NotFoundError(f"Plan change record with ID {change_id} not found")
        return PlanChangeResponse.model_validate(record)

    def list_by_subscriber(
        self, db: Session, subscriber_id: int, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[PlanChangeResponse]:
        """Fetch plan change history for a subscriber."""
        subscriber = subscriber_repo.get_by_id(db, subscriber_id)
        if not subscriber:
            raise NotFoundError(f"Subscriber with ID {subscriber_id} not found")

        offset = (page - 1) * page_size
        items, total = plan_change_repo.list_by_subscriber(
            db=db, subscriber_id=subscriber_id, offset=offset, limit=page_size
        )
        responses = [PlanChangeResponse.model_validate(pc) for pc in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )


plan_change_service = PlanChangeService()
