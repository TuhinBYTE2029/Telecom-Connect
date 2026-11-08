"""Generic base repository for SQLAlchemy 2.x models."""
from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing baseline CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(self, db: Session, id: Any) -> Optional[ModelType]:
        """Fetch entity by primary key ID."""
        return db.get(self.model, id)

    def get_all(
        self, db: Session, offset: int = 0, limit: int = 20
    ) -> List[ModelType]:
        """Fetch list of entities with offset and limit pagination."""
        stmt = select(self.model).offset(offset).limit(limit)
        return list(db.scalars(stmt).all())

    def count(self, db: Session) -> int:
        """Count total entities in table."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model)
        return db.scalar(stmt) or 0

    def create(self, db: Session, entity: ModelType) -> ModelType:
        """Add and flush entity to session."""
        db.add(entity)
        db.flush()
        db.refresh(entity)
        return entity

    def update(self, db: Session, entity: ModelType) -> ModelType:
        """Update and flush entity to session."""
        db.flush()
        db.refresh(entity)
        return entity

    def delete(self, db: Session, entity: ModelType) -> None:
        """Delete entity from session."""
        db.delete(entity)
        db.flush()
