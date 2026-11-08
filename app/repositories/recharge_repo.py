"""Recharge repository implementation."""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from app.models.recharge import Recharge
from app.models.subscription import Subscription
from app.models.enums import PaymentStatus, PaymentMethod
from app.repositories.base import BaseRepository


class RechargeRepository(BaseRepository[Recharge]):
    def __init__(self):
        super().__init__(Recharge)

    def get_by_id_with_details(self, db: Session, id: int) -> Optional[Recharge]:
        """Fetch recharge transaction with plan details."""
        stmt = (
            select(Recharge)
            .options(joinedload(Recharge.plan))
            .where(Recharge.id == id)
        )
        return db.scalars(stmt).first()

    def get_by_transaction_id(
        self, db: Session, transaction_id: str
    ) -> Optional[Recharge]:
        """Fetch recharge transaction by transaction_id."""
        stmt = (
            select(Recharge)
            .options(joinedload(Recharge.plan))
            .where(Recharge.transaction_id == transaction_id.strip())
        )
        return db.scalars(stmt).first()

    def list_recharges(
        self,
        db: Session,
        subscriber_id: Optional[int] = None,
        payment_status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Recharge], int]:
        """Filter and list recharge transactions with pagination."""
        stmt = select(Recharge).options(joinedload(Recharge.plan))
        count_stmt = select(func.count()).select_from(Recharge)

        conditions = []
        if subscriber_id is not None:
            conditions.append(Recharge.subscriber_id == subscriber_id)
        if payment_status is not None:
            conditions.append(Recharge.payment_status == payment_status)
        if payment_method is not None:
            conditions.append(Recharge.payment_method == payment_method)
        if date_from is not None:
            conditions.append(Recharge.transaction_time >= date_from)
        if date_to is not None:
            conditions.append(Recharge.transaction_time <= date_to)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(Recharge.transaction_time.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, total

    def get_active_subscription(
        self, db: Session, subscriber_id: int
    ) -> Optional[Subscription]:
        """Retrieve current active subscription for subscriber."""
        stmt = (
            select(Subscription)
            .where(
                Subscription.subscriber_id == subscriber_id,
                Subscription.is_active.is_(True),
            )
            .order_by(Subscription.end_date.desc())
        )
        return db.scalars(stmt).first()


recharge_repo = RechargeRepository()
