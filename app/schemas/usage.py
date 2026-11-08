"""UsageRecord Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field


class UsageRecordBase(BaseModel):
    subscriber_id: int
    data_used_mb: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Data consumed in MB",
    )
    call_duration_seconds: int = Field(default=0, ge=0)
    sms_sent: int = Field(default=0, ge=0)
    usage_type: str = Field(
        default="DATA",
        description="Usage category: DATA, VOICE, SMS, or MIXED",
    )


class UsageRecordCreate(UsageRecordBase):
    record_timestamp: Optional[datetime] = None


class UsageRecordResponse(UsageRecordBase):
    id: int
    record_timestamp: datetime
    created_at: datetime

    @computed_field
    def data_used_gb(self) -> float:
        """Convert recorded MB usage to GB with 2 decimal precision."""
        return round(float(self.data_used_mb) / 1024.0, 2)

    model_config = ConfigDict(from_attributes=True)


class UsageSummaryResponse(BaseModel):
    subscriber_id: int
    total_records: int
    total_data_used_mb: Decimal
    total_data_used_gb: float
    total_call_duration_seconds: int
    total_call_duration_minutes: float
    total_sms_sent: int
    first_record: Optional[datetime] = None
    last_record: Optional[datetime] = None
