"""UsageRecord repository implementation."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.usage import UsageRecord
from app.repositories.base import BaseRepository


class UsageRepository(BaseRepository[UsageRecord]):
    def __init__(self):
        super().__init__(UsageRecord)

    def list_by_subscriber(
        self,
        db: Session,
        subscriber_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        usage_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[UsageRecord], int]:
        """List subscriber usage records with date range and usage type filters."""
        stmt = select(UsageRecord).where(UsageRecord.subscriber_id == subscriber_id)
        count_stmt = (
            select(func.count())
            .select_from(UsageRecord)
            .where(UsageRecord.subscriber_id == subscriber_id)
        )

        conditions = []
        if date_from is not None:
            conditions.append(UsageRecord.record_timestamp >= date_from)
        if date_to is not None:
            conditions.append(UsageRecord.record_timestamp <= date_to)
        if usage_type is not None:
            conditions.append(
                func.upper(UsageRecord.usage_type) == usage_type.strip().upper()
            )

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = db.scalar(count_stmt) or 0
        items = list(
            db.scalars(
                stmt.order_by(UsageRecord.record_timestamp.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, total

    def get_summary(self, db: Session, subscriber_id: int) -> Dict[str, Any]:
        """Aggregate total usage metrics for a subscriber."""
        stmt = select(
            func.count(UsageRecord.id).label("total_records"),
            func.coalesce(func.sum(UsageRecord.data_used_mb), Decimal("0.00")).label(
                "total_data_mb"
            ),
            func.coalesce(func.sum(UsageRecord.call_duration_seconds), 0).label(
                "total_call_seconds"
            ),
            func.coalesce(func.sum(UsageRecord.sms_sent), 0).label("total_sms"),
            func.min(UsageRecord.record_timestamp).label("first_record"),
            func.max(UsageRecord.record_timestamp).label("last_record"),
        ).where(UsageRecord.subscriber_id == subscriber_id)

        row = db.execute(stmt).first()
        if not row:
            return {
                "total_records": 0,
                "total_data_mb": Decimal("0.00"),
                "total_call_seconds": 0,
                "total_sms": 0,
                "first_record": None,
                "last_record": None,
            }
        return {
            "total_records": row.total_records,
            "total_data_mb": row.total_data_mb,
            "total_call_seconds": row.total_call_seconds,
            "total_sms": row.total_sms,
            "first_record": row.first_record,
            "last_record": row.last_record,
        }


usage_repo = UsageRepository()
