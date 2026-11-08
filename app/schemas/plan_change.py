"""PlanChange Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PlanChangeStatus
from app.schemas.plan import PlanResponse


class PlanChangeBase(BaseModel):
    subscriber_id: int
    new_plan_id: int
    reason: Optional[str] = Field(None, max_length=255)
    status: PlanChangeStatus = PlanChangeStatus.COMPLETED


class PlanChangeCreate(BaseModel):
    subscriber_id: int
    new_plan_id: int
    reason: Optional[str] = Field(None, max_length=255)
    changed_by_user_id: Optional[int] = None
    status: Optional[PlanChangeStatus] = PlanChangeStatus.COMPLETED


class PlanChangeResponse(BaseModel):
    id: int
    subscriber_id: int
    old_plan_id: Optional[int] = None
    new_plan_id: int
    status: PlanChangeStatus
    reason: Optional[str] = None
    changed_by_user_id: Optional[int] = None
    effective_date: datetime
    created_at: datetime
    old_plan: Optional[PlanResponse] = None
    new_plan: Optional[PlanResponse] = None

    model_config = ConfigDict(from_attributes=True)
