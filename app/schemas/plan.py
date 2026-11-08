"""Prepaid Plan Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field
from app.models.enums import PlanType


class PlanBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=30, description="Unique plan code")
    name: str = Field(..., min_length=2, max_length=100)
    circle_id: Optional[int] = Field(None, description="Null for nationwide plans")
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    validity_days: int = Field(..., gt=0)
    data_allowance_mb: int = Field(default=0, ge=0, description="Allowance in MB")
    is_unlimited_data: bool = False
    talktime_minutes: int = Field(default=-1, description="-1 indicates unlimited")
    is_unlimited_calls: bool = True
    sms_count: int = Field(default=100, ge=0)
    plan_type: PlanType = PlanType.DAILY_DATA
    description: Optional[str] = None
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    circle_id: Optional[int] = None
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    validity_days: Optional[int] = Field(None, gt=0)
    data_allowance_mb: Optional[int] = Field(None, ge=0)
    is_unlimited_data: Optional[bool] = None
    talktime_minutes: Optional[int] = None
    is_unlimited_calls: Optional[bool] = None
    sms_count: Optional[int] = Field(None, ge=0)
    plan_type: Optional[PlanType] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PlanResponse(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    def data_allowance_gb(self) -> float:
        """Present MB allowance converted to GB with 2 decimal precision."""
        return round(float(self.data_allowance_mb) / 1024.0, 2)

    model_config = ConfigDict(from_attributes=True)
