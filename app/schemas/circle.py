"""TelecomCircle Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CircleBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=10, description="e.g. GJ or AHM")
    name: str = Field(..., min_length=2, max_length=100, description="e.g. Gujarat")
    state: str = Field(..., min_length=2, max_length=100, description="e.g. Gujarat")
    is_active: bool = True


class CircleCreate(CircleBase):
    pass


class CircleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


class CircleResponse(CircleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
