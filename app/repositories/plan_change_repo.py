"""PlanChange repository implementation."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from app.models.plan_change import PlanChange
from app.models.enums import PlanChangeStatus
from app.repositories.base import BaseRepository


class PlanChangeRepository(BaseRepository[PlanChange]):
    def __init__(self):
        super().__init__(PlanChange)

    def get_by_id_with_plans(self, db: Session, id: int) -> Optional[PlanChange]:
        """Fetch plan change record with old and new plan details."""
        stmt = (
            select(PlanChange)
            .options(
                joinedload(PlanChange.old_plan),
                joinedload(PlanChange.new_plan),
            )
            .where(PlanChange.id == id)
        )
        return db.scalars(stmt).first()

    def list_by_subscriber(
        self,
        db: Session,
        subscriber_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[PlanChange], int]:
        """List plan changes for a subscriber with old/new plan details."""
        stmt = (
            select(PlanChange)
            .options(
                joinedload(PlanChange.old_plan),
                joinedload(PlanChange.new_plan),
            )
            .where(PlanChange.subscriber_id == subscriber_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(PlanChange)
            .where(PlanChange.subscriber_id == subscriber_id)
        )
        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(PlanChange.created_at.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, total

    def has_pending_change(
        self, db: Session, subscriber_id: int, new_plan_id: int
    ) -> bool:
        """Check if an unresolved pending plan change already exists."""
        stmt = (
            select(func.count())
            .select_from(PlanChange)
            .where(
                PlanChange.subscriber_id == subscriber_id,
                PlanChange.new_plan_id == new_plan_id,
                PlanChange.status == PlanChangeStatus.PENDING,
            )
        )
        return (db.scalar(stmt) or 0) > 0


plan_change_repo = PlanChangeRepository()
