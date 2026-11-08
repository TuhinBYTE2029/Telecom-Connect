"""Plan database model."""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    Numeric,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import PlanType

if TYPE_CHECKING:
    from app.models.circle import TelecomCircle
    from app.models.subscription import Subscription
    from app.models.recharge import Recharge
    from app.models.plan_change import PlanChange


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    circle_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("telecom_circles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    validity_days: Mapped[int] = mapped_column(Integer, nullable=False)
    data_allowance_mb: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    is_unlimited_data: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    talktime_minutes: Mapped[int] = mapped_column(
        Integer, default=-1, nullable=False
    )
    is_unlimited_calls: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    sms_count: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    plan_type: Mapped[PlanType] = mapped_column(
        SAEnum(PlanType, native_enum=False, length=30),
        default=PlanType.DAILY_DATA,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    circle: Mapped[Optional["TelecomCircle"]] = relationship(
        "TelecomCircle", back_populates="plans"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="plan"
    )
    recharges: Mapped[List["Recharge"]] = relationship(
        "Recharge", back_populates="plan"
    )
    plan_changes_old: Mapped[List["PlanChange"]] = relationship(
        "PlanChange",
        foreign_keys="PlanChange.old_plan_id",
        back_populates="old_plan",
    )
    plan_changes_new: Mapped[List["PlanChange"]] = relationship(
        "PlanChange",
        foreign_keys="PlanChange.new_plan_id",
        back_populates="new_plan",
    )

    def __repr__(self) -> str:
        return f"<Plan id={self.id} code={self.code} price={self.price}>"
