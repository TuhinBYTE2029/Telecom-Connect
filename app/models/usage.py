"""Usage record database model."""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.subscriber import Subscriber


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    data_used_mb: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    call_duration_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    sms_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_type: Mapped[str] = mapped_column(
        String(20), default="DATA", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    subscriber: Mapped["Subscriber"] = relationship(
        "Subscriber", back_populates="usage_records"
    )

    def __repr__(self) -> str:
        return f"<UsageRecord id={self.id} subscriber_id={self.subscriber_id} data_mb={self.data_used_mb}>"
