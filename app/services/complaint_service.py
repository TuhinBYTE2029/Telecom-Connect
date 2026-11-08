"""Complaint business logic service with cross-channel deduplication."""
import uuid
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.orm import Session
from app.models.complaint import Complaint, generate_deduplication_hash
from app.models.enums import ComplaintCategory, ComplaintStatus, ComplaintChannel
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintPatch,
    ComplaintResponse,
)
from app.schemas.common import PaginatedResponse
from app.repositories.complaint_repo import complaint_repo
from app.repositories.subscriber_repo import subscriber_repo
from app.core.exceptions import NotFoundError, ConflictError


class ComplaintService:
    def create_complaint(
        self, db: Session, complaint_in: ComplaintCreate
    ) -> ComplaintResponse:
        """Create new complaint with normalized cross-channel duplicate detection."""
        subscriber = subscriber_repo.get_by_id(db, complaint_in.subscriber_id)
        if not subscriber:
            raise NotFoundError(
                f"Subscriber with ID {complaint_in.subscriber_id} not found"
            )

        # 1. Compute normalized deduplication hash for same issue on same day
        dedup_hash = generate_deduplication_hash(
            subscriber_id=subscriber.id,
            category=complaint_in.category.value,
            subject=complaint_in.subject,
            entry_date=date.today(),
        )

        # 2. Check for active duplicate submitted across any channel
        existing_duplicate = complaint_repo.find_duplicate(db, dedup_hash)
        if existing_duplicate:
            raise ConflictError(
                f"Duplicate complaint detected: Ticket '{existing_duplicate.ticket_number}' "
                f"for category '{complaint_in.category.value}' is currently {existing_duplicate.status.value} "
                f"(originally submitted via {existing_duplicate.channel.value})."
            )

        # 3. Generate unique ticket reference
        now = datetime.now(timezone.utc)
        unique_suffix = uuid.uuid4().hex[:6].upper()
        ticket_number = f"CMP-{now.strftime('%Y%m%d')}-{unique_suffix}"

        complaint = Complaint(
            ticket_number=ticket_number,
            subscriber_id=subscriber.id,
            category=complaint_in.category,
            subject=complaint_in.subject.strip(),
            description=complaint_in.description.strip(),
            channel=complaint_in.channel,
            status=ComplaintStatus.OPEN,
            deduplication_hash=dedup_hash,
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return ComplaintResponse.model_validate(complaint)

    def get_complaint(self, db: Session, complaint_id: int) -> ComplaintResponse:
        """Fetch complaint details by ID."""
        complaint = complaint_repo.get_by_id(db, complaint_id)
        if not complaint:
            raise NotFoundError(f"Complaint with ID {complaint_id} not found")
        return ComplaintResponse.model_validate(complaint)

    def list_complaints(
        self,
        db: Session,
        subscriber_id: Optional[int] = None,
        category: Optional[ComplaintCategory] = None,
        status: Optional[ComplaintStatus] = None,
        channel: Optional[ComplaintChannel] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ComplaintResponse]:
        """List complaints with filters and pagination."""
        offset = (page - 1) * page_size
        items, total = complaint_repo.list_complaints(
            db=db,
            subscriber_id=subscriber_id,
            category=category,
            status=status,
            channel=channel,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=page_size,
        )
        responses = [ComplaintResponse.model_validate(c) for c in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )

    def patch_complaint(
        self, db: Session, complaint_id: int, patch_in: ComplaintPatch
    ) -> ComplaintResponse:
        """Update complaint status, staff assignment, and resolution notes."""
        complaint = complaint_repo.get_by_id(db, complaint_id)
        if not complaint:
            raise NotFoundError(f"Complaint with ID {complaint_id} not found")

        update_data = patch_in.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            complaint.status = new_status
            if new_status in (
                ComplaintStatus.RESOLVED,
                ComplaintStatus.CLOSED,
                ComplaintStatus.REJECTED,
            ):
                complaint.resolved_at = datetime.now(timezone.utc)
            else:
                complaint.resolved_at = None

        if "assigned_staff_id" in update_data:
            complaint.assigned_staff_id = update_data["assigned_staff_id"]

        if "resolution_notes" in update_data and update_data["resolution_notes"] is not None:
            complaint.resolution_notes = update_data["resolution_notes"].strip()

        db.commit()
        db.refresh(complaint)
        return ComplaintResponse.model_validate(complaint)


complaint_service = ComplaintService()
