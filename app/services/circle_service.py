"""TelecomCircle business logic service."""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.circle import TelecomCircle
from app.schemas.circle import CircleCreate, CircleUpdate, CircleResponse
from app.schemas.common import PaginatedResponse
from app.repositories.circle_repo import circle_repo
from app.core.exceptions import NotFoundError, ConflictError


class CircleService:
    def create_circle(self, db: Session, circle_in: CircleCreate) -> CircleResponse:
        """Create new telecom circle with uniqueness validation."""
        existing = circle_repo.get_by_code(db, circle_in.code)
        if existing:
            raise ConflictError(
                f"Telecom circle with code '{circle_in.code.upper()}' already exists"
            )

        circle = TelecomCircle(
            code=circle_in.code.strip().upper(),
            name=circle_in.name.strip(),
            state=circle_in.state.strip(),
            is_active=circle_in.is_active,
        )
        db.add(circle)
        db.commit()
        db.refresh(circle)
        return CircleResponse.model_validate(circle)

    def get_circle(self, db: Session, circle_id: int) -> CircleResponse:
        """Fetch circle by ID or raise NotFoundError."""
        circle = circle_repo.get_by_id(db, circle_id)
        if not circle:
            raise NotFoundError(f"Telecom circle with ID {circle_id} not found")
        return CircleResponse.model_validate(circle)

    def list_circles(
        self,
        db: Session,
        search: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[CircleResponse]:
        """List circles with pagination and filters."""
        offset = (page - 1) * page_size
        items, total = circle_repo.search_and_filter(
            db=db,
            search=search,
            state=state,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        responses = [CircleResponse.model_validate(c) for c in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )

    def update_circle(
        self, db: Session, circle_id: int, circle_in: CircleUpdate
    ) -> CircleResponse:
        """Update circle attributes."""
        circle = circle_repo.get_by_id(db, circle_id)
        if not circle:
            raise NotFoundError(f"Telecom circle with ID {circle_id} not found")

        update_data = circle_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None and isinstance(value, str):
                value = value.strip()
            setattr(circle, field, value)

        db.commit()
        db.refresh(circle)
        return CircleResponse.model_validate(circle)

    def delete_circle(self, db: Session, circle_id: int) -> None:
        """Safely delete circle verifying no foreign references."""
        circle = circle_repo.get_by_id(db, circle_id)
        if not circle:
            raise NotFoundError(f"Telecom circle with ID {circle_id} not found")

        if circle_repo.has_subscribers(db, circle_id):
            raise ConflictError(
                "Cannot delete circle: subscribers are registered in this circle"
            )
        if circle_repo.has_plans(db, circle_id):
            raise ConflictError(
                "Cannot delete circle: active prepaid plans are assigned to this circle"
            )

        db.delete(circle)
        db.commit()


circle_service = CircleService()
