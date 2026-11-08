"""TelecomCircle repository implementation."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.circle import TelecomCircle
from app.models.subscriber import Subscriber
from app.models.plan import Plan
from app.repositories.base import BaseRepository


class CircleRepository(BaseRepository[TelecomCircle]):
    def __init__(self):
        super().__init__(TelecomCircle)

    def get_by_code(self, db: Session, code: str) -> Optional[TelecomCircle]:
        """Fetch circle by its unique code (case-insensitive)."""
        stmt = select(TelecomCircle).where(
            func.upper(TelecomCircle.code) == code.strip().upper()
        )
        return db.scalars(stmt).first()

    def search_and_filter(
        self,
        db: Session,
        search: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[TelecomCircle], int]:
        """Search and filter telecom circles with pagination and count."""
        stmt = select(TelecomCircle)
        count_stmt = select(func.count()).select_from(TelecomCircle)

        conditions = []
        if search:
            search_term = f"%{search.strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(TelecomCircle.name).like(search_term),
                    func.lower(TelecomCircle.code).like(search_term),
                    func.lower(TelecomCircle.state).like(search_term),
                )
            )
        if state:
            conditions.append(
                func.lower(TelecomCircle.state) == state.strip().lower()
            )
        if is_active is not None:
            conditions.append(TelecomCircle.is_active == is_active)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(TelecomCircle.name.asc()).offset(offset).limit(limit)
            ).all()
        )
        return items, total

    def has_subscribers(self, db: Session, circle_id: int) -> bool:
        """Check if circle has registered subscribers."""
        stmt = (
            select(func.count())
            .select_from(Subscriber)
            .where(Subscriber.circle_id == circle_id)
        )
        return (db.scalar(stmt) or 0) > 0

    def has_plans(self, db: Session, circle_id: int) -> bool:
        """Check if circle has assigned plans."""
        stmt = (
            select(func.count())
            .select_from(Plan)
            .where(Plan.circle_id == circle_id)
        )
        return (db.scalar(stmt) or 0) > 0


circle_repo = CircleRepository()
