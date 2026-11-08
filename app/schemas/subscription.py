"""Subscription Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.plan import PlanResponse


class SubscriptionBase(BaseModel):
    subscriber_id: int
    plan_id: int
    auto_renew: bool = False


class SubscriptionCreate(SubscriptionBase):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    plan: Optional[PlanResponse] = None

    model_config = ConfigDict(from_attributes=True)
