"""Prepaid Plan business logic service."""
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.plan import Plan
from app.models.enums import PlanType
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.schemas.common import PaginatedResponse
from app.repositories.plan_repo import plan_repo
from app.repositories.circle_repo import circle_repo
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError


class PlanService:
    def create_plan(self, db: Session, plan_in: PlanCreate) -> PlanResponse:
        """Create new prepaid plan with domain validation."""
        existing = plan_repo.get_by_code(db, plan_in.code)
        if existing:
            raise ConflictError(f"Plan with code '{plan_in.code}' already exists")

        if plan_in.circle_id is not None:
            circle = circle_repo.get_by_id(db, plan_in.circle_id)
            if not circle:
                raise NotFoundError(
                    f"Telecom circle with ID {plan_in.circle_id} not found"
                )

        if plan_in.price <= Decimal("0.00"):
            raise BadRequestError("Plan price must be greater than zero")
        if plan_in.validity_days <= 0:
            raise BadRequestError("Plan validity must be at least 1 day")

        plan = Plan(
            code=plan_in.code.strip().upper(),
            name=plan_in.name.strip(),
            circle_id=plan_in.circle_id,
            price=plan_in.price,
            validity_days=plan_in.validity_days,
            data_allowance_mb=plan_in.data_allowance_mb,
            is_unlimited_data=plan_in.is_unlimited_data,
            talktime_minutes=plan_in.talktime_minutes,
            is_unlimited_calls=plan_in.is_unlimited_calls,
            sms_count=plan_in.sms_count,
            plan_type=plan_in.plan_type,
            description=plan_in.description.strip() if plan_in.description else None,
            is_active=plan_in.is_active,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return PlanResponse.model_validate(plan)

    def get_plan(self, db: Session, plan_id: int) -> PlanResponse:
        """Fetch plan by ID or raise NotFoundError."""
        plan = plan_repo.get_by_id(db, plan_id)
        if not plan:
            raise NotFoundError(f"Prepaid plan with ID {plan_id} not found")
        return PlanResponse.model_validate(plan)

    def list_plans(
        self,
        db: Session,
        search: Optional[str] = None,
        circle_id: Optional[int] = None,
        plan_type: Optional[PlanType] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_validity: Optional[int] = None,
        max_validity: Optional[int] = None,
        min_data_mb: Optional[int] = None,
        max_data_mb: Optional[int] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[PlanResponse]:
        """List and filter prepaid plans with pagination."""
        offset = (page - 1) * page_size
        items, total = plan_repo.search_and_filter(
            db=db,
            search=search,
            circle_id=circle_id,
            plan_type=plan_type,
            min_price=min_price,
            max_price=max_price,
            min_validity=min_validity,
            max_validity=max_validity,
            min_data_mb=min_data_mb,
            max_data_mb=max_data_mb,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        responses = [PlanResponse.model_validate(p) for p in items]
        return PaginatedResponse.create(
            items=responses, total=total, page=page, page_size=page_size
        )

    def update_plan(
        self, db: Session, plan_id: int, plan_in: PlanUpdate
    ) -> PlanResponse:
        """Update prepaid plan attributes."""
        plan = plan_repo.get_by_id(db, plan_id)
        if not plan:
            raise NotFoundError(f"Prepaid plan with ID {plan_id} not found")

        update_data = plan_in.model_dump(exclude_unset=True)
        if "circle_id" in update_data and update_data["circle_id"] is not None:
            circle = circle_repo.get_by_id(db, update_data["circle_id"])
            if not circle:
                raise NotFoundError(
                    f"Telecom circle with ID {update_data['circle_id']} not found"
                )

        if "price" in update_data and update_data["price"] is not None:
            if update_data["price"] <= Decimal("0.00"):
                raise BadRequestError("Plan price must be greater than zero")

        if "validity_days" in update_data and update_data["validity_days"] is not None:
            if update_data["validity_days"] <= 0:
                raise BadRequestError("Plan validity must be at least 1 day")

        for field, value in update_data.items():
            if value is not None and isinstance(value, str):
                value = value.strip()
            setattr(plan, field, value)

        db.commit()
        db.refresh(plan)
        return PlanResponse.model_validate(plan)

    def delete_or_deactivate_plan(
        self, db: Session, plan_id: int
    ) -> dict:
        """Safely deactivates plan if active subscribers exist, or deletes if unreferenced."""
        plan = plan_repo.get_by_id(db, plan_id)
        if not plan:
            raise NotFoundError(f"Prepaid plan with ID {plan_id} not found")

        has_active_subs = plan_repo.has_active_subscriptions(db, plan_id)
        if has_active_subs:
            plan.is_active = False
            db.commit()
            return {
                "message": f"Plan '{plan.code}' has active subscriptions; safely deactivated instead of deleted.",
                "action": "deactivated",
            }

        db.delete(plan)
        db.commit()
        return {
            "message": f"Plan '{plan.code}' deleted successfully.",
            "action": "deleted",
        }


plan_service = PlanService()
