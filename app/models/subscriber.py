"""Subscriber database model."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import SubscriberStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.circle import TelecomCircle
    from app.models.subscription import Subscription
    from app.models.recharge import Recharge
    from app.models.usage import UsageRecord
    from app.models.complaint import Complaint
    from app.models.plan_change import PlanChange


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    circle_id: Mapped[int] = mapped_column(
        ForeignKey("telecom_circles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    mobile_number: Mapped[str] = mapped_column(
        String(15), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), index=True, nullable=True
    )
    status: Mapped[SubscriberStatus] = mapped_column(
        SAEnum(SubscriberStatus, native_enum=False, length=20),
        default=SubscriberStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    sim_card_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    activation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ported_out_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="subscriber"
    )
    circle: Mapped["TelecomCircle"] = relationship(
        "TelecomCircle", back_populates="subscribers"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="subscriber", cascade="all, delete-orphan"
    )
    recharges: Mapped[List["Recharge"]] = relationship(
        "Recharge", back_populates="subscriber", cascade="all, delete-orphan"
    )
    usage_records: Mapped[List["UsageRecord"]] = relationship(
        "UsageRecord", back_populates="subscriber", cascade="all, delete-orphan"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint", back_populates="subscriber", cascade="all, delete-orphan"
    )
    plan_changes: Mapped[List["PlanChange"]] = relationship(
        "PlanChange", back_populates="subscriber", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subscriber id={self.id} mobile={self.mobile_number} status={self.status}>"
