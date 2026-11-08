"""UsageRecord business logic service."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.usage import UsageRecord
from app.schemas.usage import (
    UsageRecordCreate,
    UsageRecordResponse,
    UsageSummaryResponse,
)
from app.schemas.common import PaginatedResponse
from app.repositories.usage_repo import usage_repo
from app.repositories.subscriber_repo import subscriber_repo
from app.core.exceptions import NotFoundError, BadRequestError


class UsageService:
    def record_usage(
        self, db: Session, usage_in: UsageRecordCreate
    ) -> UsageRecordResponse:
        """Record data, voice, or SMS usage with positive value validation."""
        subscriber = subscriber_repo.get_by_id(db, usage_in.subscriber_id)
        if not subscriber:
            raise NotFoundError(
                f"Subscriber with ID {usage_in.subscriber_id} not found"
            )

        if (
            usage_in.data_used_mb <= Decimal("0.00")
            and usage_in.call_duration_seconds <= 0
            and usage_in.sms_sent <= 0
        ):
            raise BadRequestError(
                "At least one usage metric (data_used_mb, call_duration_seconds, sms_sent) must be greater than zero"
            )

        # Infer usage type if default
        usage_type = usage_in.usage_type
        if usage_type == "DATA":
            if (
                usage_in.call_duration_seconds > 0
                and usage_in.data_used_mb == Decimal("0.00")
                and usage_in.sms_sent == 0
            ):
                usage_type = "VOICE"
            elif (
                usage_in.sms_sent > 0
                and usage_in.data_used_mb == Decimal("0.00")
                and usage_in.call_duration_seconds == 0
            ):
                usage_type = "SMS"
            elif (
                int(usage_in.data_used_mb > 0)
                + int(usage_in.call_duration_seconds > 0)
                + int(usage_in.sms_sent > 0)
            ) > 1:
                usage_type = "MIXED"

        now = datetime.now(timezone.utc)
        record = UsageRecord(
            subscriber_id=subscriber.id,
            data_used_mb=usage_in.data_used_mb,
            call_duration_seconds=usage_in.call_duration_seconds,
            sms_sent=usage_in.sms_sent,
            usage_type=usage_type.upper(),
            record_timestamp=usage_in.record_timestamp or now,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return UsageRecordResponse.model_validate(record)

    def list_usage(
        self,
        db: Session,
        subscriber_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        usage_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[UsageRecordResponse]:
        """Retrieve paginated usage records for a subscriber."""
        subscriber = subscriber_repo.get_by_id(db, subscriber_id)
        if not subscriber:
            raise NotFoundError(f"Subscriber with ID {subscriber_id} not found")

        offset = (page - 1) * page_size
        items, total = usage_repo.list_by_subscriber(
            db=db,
            subscriber_id=subscriber_id,
            date_from=date_from,
            date_to=date_to,
            usage_type=usage_type,
            offset=offset,
            limit=page_size,
        )
        responses = [UsageRecordResponse.model_validate(u) for u in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )

    def get_summary(
        self, db: Session, subscriber_id: int
    ) -> UsageSummaryResponse:
        """Calculate aggregated total data (MB/GB), call time, and SMS counts."""
        subscriber = subscriber_repo.get_by_id(db, subscriber_id)
        if not subscriber:
            raise NotFoundError(f"Subscriber with ID {subscriber_id} not found")

        summary = usage_repo.get_summary(db, subscriber_id)
        total_data_mb = summary["total_data_mb"]
        total_data_gb = round(float(total_data_mb) / 1024.0, 2)
        total_call_sec = summary["total_call_seconds"]
        total_call_min = round(float(total_call_sec) / 60.0, 2)

        return UsageSummaryResponse(
            subscriber_id=subscriber_id,
            total_records=summary["total_records"],
            total_data_used_mb=total_data_mb,
            total_data_used_gb=total_data_gb,
            total_call_duration_seconds=total_call_sec,
            total_call_duration_minutes=total_call_min,
            total_sms_sent=summary["total_sms"],
            first_record=summary["first_record"],
            last_record=summary["last_record"],
        )


usage_service = UsageService()
