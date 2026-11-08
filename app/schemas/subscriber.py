"""Subscriber Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.models.enums import SubscriberStatus
from app.schemas.circle import CircleResponse


class SubscriberBase(BaseModel):
    circle_id: int
    mobile_number: str = Field(
        ...,
        pattern=r"^[6-9]\d{9}$",
        description="10-digit Indian mobile number starting with 6-9",
    )
    full_name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    sim_card_number: str = Field(..., min_length=15, max_length=30)
    status: SubscriberStatus = SubscriberStatus.ACTIVE


class SubscriberCreate(SubscriberBase):
    user_id: Optional[int] = None


class SubscriberUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    status: Optional[SubscriberStatus] = None
    circle_id: Optional[int] = None


class SubscriberResponse(SubscriberBase):
    id: int
    user_id: Optional[int] = None
    activation_date: datetime
    ported_out_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriberDetailResponse(SubscriberResponse):
    circle: Optional[CircleResponse] = None
