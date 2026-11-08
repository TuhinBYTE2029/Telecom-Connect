"""Unit tests for Pydantic schema validation and computed presentation fields."""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import ValidationError
from app.schemas import (
    UserCreate,
    UserResponse,
    CircleCreate,
    PlanCreate,
    PlanResponse,
    SubscriberCreate,
    SubscriberResponse,
    RechargeCreate,
    RechargeResponse,
    UsageRecordCreate,
    UsageRecordResponse,
    ComplaintCreate,
    ComplaintResponse,
    PaginationParams,
    PaginatedResponse,
)
from app.models.enums import (
    UserRole,
    SubscriberStatus,
    PlanType,
    PaymentMethod,
    PaymentStatus,
    ComplaintCategory,
    ComplaintStatus,
    ComplaintChannel,
)


def test_user_schema_validation():
    """Test user schema validation rules."""
    user_in = UserCreate(
        email="valid@example.com",
        full_name="Valid User",
        password="ValidPassword123",
        role=UserRole.SUBSCRIBER,
    )
    assert user_in.email == "valid@example.com"

    # Invalid email format
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            full_name="Invalid",
            password="short",
        )


def test_subscriber_mobile_validation():
    """Test 10-digit Indian mobile number validation."""
    sub_in = SubscriberCreate(
        circle_id=1,
        mobile_number="9825012345",
        full_name="Aarav Patel",
        sim_card_number="8991001234567890123",
    )
    assert sub_in.mobile_number == "9825012345"

    # Number starting with invalid digit (e.g. 5) or short length
    with pytest.raises(ValidationError):
        SubscriberCreate(
            circle_id=1,
            mobile_number="5825012345",
            full_name="Invalid Mobile",
            sim_card_number="8991001234567890123",
        )

    with pytest.raises(ValidationError):
        SubscriberCreate(
            circle_id=1,
            mobile_number="9825012",
            full_name="Short Mobile",
            sim_card_number="8991001234567890123",
        )


def test_plan_mb_to_gb_computed_field():
    """Test data_allowance_gb computed field in PlanResponse."""
    now = datetime.now(timezone.utc)
    plan_resp = PlanResponse(
        id=1,
        code="TC-GJ-299",
        name="Gujarat 299",
        price=Decimal("299.00"),
        validity_days=28,
        data_allowance_mb=2048,  # Exactly 2 GB
        is_unlimited_data=False,
        talktime_minutes=-1,
        is_unlimited_calls=True,
        sms_count=100,
        plan_type=PlanType.DAILY_DATA,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    assert plan_resp.data_allowance_gb == 2.0

    plan_resp_15gb = PlanResponse(
        id=2,
        code="TC-GJ-199",
        name="Gujarat 199",
        price=Decimal("199.00"),
        validity_days=28,
        data_allowance_mb=1536,  # 1.5 GB
        is_unlimited_data=False,
        talktime_minutes=-1,
        is_unlimited_calls=True,
        sms_count=100,
        plan_type=PlanType.DAILY_DATA,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    assert plan_resp_15gb.data_allowance_gb == 1.5


def test_usage_record_mb_to_gb_computed_field():
    """Test data_used_gb computed field in UsageRecordResponse."""
    now = datetime.now(timezone.utc)
    usage_resp = UsageRecordResponse(
        id=1,
        subscriber_id=10,
        data_used_mb=Decimal("3072.00"),  # Exactly 3 GB
        call_duration_seconds=500,
        sms_sent=4,
        record_timestamp=now,
        created_at=now,
    )
    assert usage_resp.data_used_gb == 3.0


def test_pagination_params_and_response():
    """Test pagination math and PaginatedResponse helper."""
    params = PaginationParams(page=2, page_size=25)
    assert params.offset == 25
    assert params.limit == 25

    page_resp = PaginatedResponse.create(
        items=["item1", "item2"], total=55, page=2, page_size=25
    )
    assert page_resp.total == 55
    assert page_resp.page == 2
    assert page_resp.total_pages == 3
