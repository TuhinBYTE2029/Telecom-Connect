"""Plan repository implementation."""
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.plan import Plan
from app.models.enums import PlanType
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    def __init__(self):
        super().__init__(Plan)

    def get_by_code(self, db: Session, code: str) -> Optional[Plan]:
        """Fetch plan by unique code (case-insensitive)."""
        stmt = select(Plan).where(
            func.upper(Plan.code) == code.strip().upper()
        )
        return db.scalars(stmt).first()

    def search_and_filter(
        self,
        db: Session,
        search: Optional[str] = None,
        circle_id: Optional[int] = None,
        plan_type: Optional[PlanType] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_validity: Optional[int] = None,
        max_validity: Optional[int] = None,
        min_data_mb: Optional[int] = None,
        max_data_mb: Optional[int] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Plan], int]:
        """Search and filter plans with multiple criteria and pagination."""
        stmt = select(Plan)
        count_stmt = select(func.count()).select_from(Plan)

        conditions = []
        if search:
            search_term = f"%{search.strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(Plan.name).like(search_term),
                    func.lower(Plan.code).like(search_term),
                    func.lower(Plan.description).like(search_term),
                )
            )
        if circle_id is not None:
            # Match circle specific or national plans (circle_id is None)
            conditions.append(
                or_(Plan.circle_id == circle_id, Plan.circle_id.is_(None))
            )
        if plan_type is not None:
            conditions.append(Plan.plan_type == plan_type)
        if min_price is not None:
            conditions.append(Plan.price >= min_price)
        if max_price is not None:
            conditions.append(Plan.price <= max_price)
        if min_validity is not None:
            conditions.append(Plan.validity_days >= min_validity)
        if max_validity is not None:
            conditions.append(Plan.validity_days <= max_validity)
        if min_data_mb is not None:
            conditions.append(Plan.data_allowance_mb >= min_data_mb)
        if max_data_mb is not None:
            conditions.append(Plan.data_allowance_mb <= max_data_mb)
        if is_active is not None:
            conditions.append(Plan.is_active == is_active)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(Plan.price.asc(), Plan.name.asc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, total

    def has_active_subscriptions(self, db: Session, plan_id: int) -> bool:
        """Check if plan currently has active subscriptions."""
        stmt = (
            select(func.count())
            .select_from(Subscription)
            .where(
                Subscription.plan_id == plan_id,
                Subscription.is_active.is_(True),
            )
        )
        return (db.scalar(stmt) or 0) > 0


plan_repo = PlanRepository()
