"""Subscriber repository implementation."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.subscriber import Subscriber
from app.models.enums import SubscriberStatus
from app.repositories.base import BaseRepository


class SubscriberRepository(BaseRepository[Subscriber]):
    def __init__(self):
        super().__init__(Subscriber)

    def get_by_id_with_circle(self, db: Session, id: int) -> Optional[Subscriber]:
        """Fetch subscriber by ID with eager loaded telecom circle."""
        stmt = (
            select(Subscriber)
            .options(joinedload(Subscriber.circle))
            .where(Subscriber.id == id)
        )
        return db.scalars(stmt).first()

    def get_by_mobile(
        self, db: Session, mobile_number: str
    ) -> Optional[Subscriber]:
        """Fetch subscriber by mobile number."""
        stmt = (
            select(Subscriber)
            .options(joinedload(Subscriber.circle))
            .where(Subscriber.mobile_number == mobile_number.strip())
        )
        return db.scalars(stmt).first()

    def get_by_sim(
        self, db: Session, sim_card_number: str
    ) -> Optional[Subscriber]:
        """Fetch subscriber by SIM card number."""
        stmt = select(Subscriber).where(
            Subscriber.sim_card_number == sim_card_number.strip()
        )
        return db.scalars(stmt).first()

    def search_and_filter(
        self,
        db: Session,
        search: Optional[str] = None,
        status: Optional[SubscriberStatus] = None,
        circle_id: Optional[int] = None,
        exclude_ported_out: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Subscriber], int]:
        """Search and filter subscribers with pagination."""
        stmt = select(Subscriber).options(joinedload(Subscriber.circle))
        count_stmt = select(func.count()).select_from(Subscriber)

        conditions = []
        if search:
            search_term = f"%{search.strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(Subscriber.full_name).like(search_term),
                    Subscriber.mobile_number.like(search_term),
                    func.lower(Subscriber.email).like(search_term),
                    Subscriber.sim_card_number.like(search_term),
                )
            )
        if status is not None:
            conditions.append(Subscriber.status == status)
        elif exclude_ported_out:
            conditions.append(Subscriber.status != SubscriberStatus.PORTED_OUT)

        if circle_id is not None:
            conditions.append(Subscriber.circle_id == circle_id)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(Subscriber.created_at.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, total


subscriber_repo = SubscriberRepository()
