"""Recharge transaction Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PaymentMethod, PaymentStatus
from app.schemas.plan import PlanResponse


class RechargeBase(BaseModel):
    subscriber_id: int
    plan_id: int
    amount: Optional[Decimal] = Field(
        None, gt=0, max_digits=10, decimal_places=2, description="Optional; defaults to plan price if omitted"
    )
    payment_method: PaymentMethod = PaymentMethod.UPI


class RechargeCreate(RechargeBase):
    simulate_failure: bool = Field(
        default=False, description="Simulate payment gateway failure for testing"
    )
    failure_reason: Optional[str] = Field(
        None, description="Optional reason when simulating failed transactions"
    )


class RechargeResponse(BaseModel):
    id: int
    transaction_id: str
    subscriber_id: int
    plan_id: int
    amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    failure_reason: Optional[str] = None
    transaction_time: datetime
    created_at: datetime
    updated_at: datetime
    plan: Optional[PlanResponse] = None

    model_config = ConfigDict(from_attributes=True)
