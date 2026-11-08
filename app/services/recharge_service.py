"""Recharge business logic service."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.recharge import Recharge
from app.models.subscription import Subscription
from app.models.enums import SubscriberStatus, PaymentStatus, PaymentMethod
from app.schemas.recharge import RechargeCreate, RechargeResponse
from app.schemas.common import PaginatedResponse
from app.repositories.recharge_repo import recharge_repo
from app.repositories.subscriber_repo import subscriber_repo
from app.repositories.plan_repo import plan_repo
from app.core.exceptions import NotFoundError, BadRequestError


class RechargeService:
    def create_recharge(
        self, db: Session, recharge_in: RechargeCreate
    ) -> RechargeResponse:
        """Create recharge transaction with eligibility validation, payment simulation, and subscription extension."""
        # 1. Validate subscriber
        subscriber = subscriber_repo.get_by_id(db, recharge_in.subscriber_id)
        if not subscriber:
            raise NotFoundError(
                f"Subscriber with ID {recharge_in.subscriber_id} not found"
            )

        if subscriber.status == SubscriberStatus.PORTED_OUT:
            raise BadRequestError("Ported-out subscribers cannot be recharged")
        if subscriber.status == SubscriberStatus.SUSPENDED:
            raise BadRequestError("Suspended subscribers cannot be recharged")

        # 2. Validate plan
        plan = plan_repo.get_by_id(db, recharge_in.plan_id)
        if not plan:
            raise NotFoundError(f"Plan with ID {recharge_in.plan_id} not found")
        if not plan.is_active:
            raise BadRequestError(f"Prepaid plan '{plan.code}' is inactive")

        # 3. Validate recharge amount
        amount = recharge_in.amount if recharge_in.amount is not None else plan.price
        if amount != plan.price:
            raise BadRequestError(
                f"Recharge amount INR {amount} does not match plan price INR {plan.price}"
            )

        # 4. Generate unique transaction reference
        now = datetime.now(timezone.utc)
        unique_suffix = uuid.uuid4().hex[:8].upper()
        transaction_id = f"TXN-{now.strftime('%Y%m%d%H%M%S')}-{unique_suffix}"

        # 5. Simulate payment processing
        if recharge_in.simulate_failure:
            payment_status = PaymentStatus.FAILED
            failure_reason = (
                recharge_in.failure_reason
                or "Payment declined by issuing bank (simulated failure)"
            )
        else:
            payment_status = PaymentStatus.SUCCESS
            failure_reason = None

        recharge = Recharge(
            transaction_id=transaction_id,
            subscriber_id=subscriber.id,
            plan_id=plan.id,
            amount=amount,
            payment_method=recharge_in.payment_method,
            payment_status=payment_status,
            failure_reason=failure_reason,
            transaction_time=now,
        )
        db.add(recharge)

        # 6. Update subscription ONLY upon successful payment within transaction
        if payment_status == PaymentStatus.SUCCESS:
            active_sub = recharge_repo.get_active_subscription(db, subscriber.id)
            if active_sub:
                base_start = (
                    active_sub.end_date
                    if active_sub.end_date and active_sub.end_date > now
                    else now
                )
                active_sub.end_date = base_start + timedelta(days=plan.validity_days)
                active_sub.plan_id = plan.id
            else:
                new_sub = Subscription(
                    subscriber_id=subscriber.id,
                    plan_id=plan.id,
                    start_date=now,
                    end_date=now + timedelta(days=plan.validity_days),
                    is_active=True,
                    auto_renew=False,
                )
                db.add(new_sub)

        db.commit()
        db.refresh(recharge)
        return RechargeResponse.model_validate(recharge)

    def get_recharge(self, db: Session, recharge_id: int) -> RechargeResponse:
        """Fetch recharge details by ID."""
        recharge = recharge_repo.get_by_id_with_details(db, recharge_id)
        if not recharge:
            raise NotFoundError(f"Recharge transaction with ID {recharge_id} not found")
        return RechargeResponse.model_validate(recharge)

    def list_recharges(
        self,
        db: Session,
        subscriber_id: Optional[int] = None,
        payment_status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[RechargeResponse]:
        """List recharge transactions with filters and pagination."""
        offset = (page - 1) * page_size
        items, total = recharge_repo.list_recharges(
            db=db,
            subscriber_id=subscriber_id,
            payment_status=payment_status,
            payment_method=payment_method,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=page_size,
        )
        responses = [RechargeResponse.model_validate(r) for r in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )


recharge_service = RechargeService()
