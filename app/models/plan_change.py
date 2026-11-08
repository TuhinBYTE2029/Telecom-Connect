"""PlanChange database model for tracking plan migration history."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

from app.models.enums import PlanChangeStatus

if TYPE_CHECKING:
    from app.models.subscriber import Subscriber
    from app.models.plan import Plan
    from app.models.user import User


class PlanChange(Base):
    __tablename__ = "plan_changes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    new_plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[PlanChangeStatus] = mapped_column(
        String(20),
        default=PlanChangeStatus.COMPLETED,
        nullable=False,
        index=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    effective_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    subscriber: Mapped["Subscriber"] = relationship(
        "Subscriber", back_populates="plan_changes"
    )
    old_plan: Mapped[Optional["Plan"]] = relationship(
        "Plan", foreign_keys=[old_plan_id], back_populates="plan_changes_old"
    )
    new_plan: Mapped["Plan"] = relationship(
        "Plan", foreign_keys=[new_plan_id], back_populates="plan_changes_new"
    )
    changed_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[changed_by_user_id], back_populates="plan_changes_made"
    )

    def __repr__(self) -> str:
        return f"<PlanChange id={self.id} subscriber_id={self.subscriber_id} old={self.old_plan_id} new={self.new_plan_id}>"
