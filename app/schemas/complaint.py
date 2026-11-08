"""Complaint Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ComplaintCategory, ComplaintStatus, ComplaintChannel


class ComplaintBase(BaseModel):
    subscriber_id: int
    category: ComplaintCategory
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    channel: ComplaintChannel = ComplaintChannel.APP


class ComplaintCreate(ComplaintBase):
    pass


class ComplaintPatch(BaseModel):
    status: Optional[ComplaintStatus] = None
    assigned_staff_id: Optional[int] = None
    resolution_notes: Optional[str] = None


class ComplaintUpdate(ComplaintPatch):
    pass


class ComplaintResponse(ComplaintBase):
    id: int
    ticket_number: str
    status: ComplaintStatus
    deduplication_hash: str
    assigned_staff_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
