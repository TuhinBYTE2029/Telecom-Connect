"""Complaint database model."""
import hashlib
from datetime import datetime, date
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import ComplaintCategory, ComplaintStatus, ComplaintChannel

if TYPE_CHECKING:
    from app.models.subscriber import Subscriber


def generate_deduplication_hash(
    subscriber_id: int,
    category: str,
    subject: str,
    entry_date: Optional[date] = None,
) -> str:
    """Generate SHA-256 hash to detect duplicate complaints across channels for same issue on same day."""
    if entry_date is None:
        entry_date = date.today()
    normalized_subject = " ".join(subject.strip().lower().split())
    raw_str = f"{subscriber_id}:{category}:{normalized_subject}:{entry_date.isoformat()}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[ComplaintCategory] = mapped_column(
        SAEnum(ComplaintCategory, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(ComplaintStatus, native_enum=False, length=20),
        default=ComplaintStatus.OPEN,
        nullable=False,
        index=True,
    )
    channel: Mapped[ComplaintChannel] = mapped_column(
        SAEnum(ComplaintChannel, native_enum=False, length=20),
        default=ComplaintChannel.APP,
        nullable=False,
    )
    deduplication_hash: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )
    assigned_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    subscriber: Mapped["Subscriber"] = relationship(
        "Subscriber", back_populates="complaints"
    )
    assigned_staff: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_staff_id]
    )

    def __repr__(self) -> str:
        return f"<Complaint id={self.id} ticket={self.ticket_number} status={self.status}>"
