"""Complaint repository implementation."""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.models.enums import ComplaintCategory, ComplaintStatus, ComplaintChannel
from app.repositories.base import BaseRepository


class ComplaintRepository(BaseRepository[Complaint]):
    def __init__(self):
        super().__init__(Complaint)

    def get_by_ticket_number(
        self, db: Session, ticket_number: str
    ) -> Optional[Complaint]:
        """Fetch complaint by ticket number."""
        stmt = select(Complaint).where(
            Complaint.ticket_number == ticket_number.strip()
        )
        return db.scalars(stmt).first()

    def find_duplicate(
        self, db: Session, deduplication_hash: str
    ) -> Optional[Complaint]:
        """Find an active duplicate complaint with matching deduplication hash."""
        stmt = (
            select(Complaint)
            .where(
                Complaint.deduplication_hash == deduplication_hash,
                Complaint.status.in_([ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS]),
            )
            .order_by(Complaint.created_at.desc())
        )
        return db.scalars(stmt).first()

    def list_complaints(
        self,
        db: Session,
        subscriber_id: Optional[int] = None,
        category: Optional[ComplaintCategory] = None,
        status: Optional[ComplaintStatus] = None,
        channel: Optional[ComplaintChannel] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Complaint], int]:
        """List and filter complaints with pagination."""
        stmt = select(Complaint)
        count_stmt = select(func.count()).select_from(Complaint)

        conditions = []
        if subscriber_id is not None:
            conditions.append(Complaint.subscriber_id == subscriber_id)
        if category is not None:
            conditions.append(Complaint.category == category)
        if status is not None:
            conditions.append(Complaint.status == status)
        if channel is not None:
            conditions.append(Complaint.channel == channel)
        if date_from is not None:
            conditions.append(Complaint.created_at >= date_from)
        if date_to is not None:
            conditions.append(Complaint.created_at <= date_to)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(Complaint.created_at.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, total


complaint_repo = ComplaintRepository()
