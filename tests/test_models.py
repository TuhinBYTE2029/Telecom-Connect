"""Unit tests for all 9 database entities, constraints, and relationships."""
import pytest
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models import (
    User,
    UserRole,
    TelecomCircle,
    Plan,
    PlanType,
    Subscriber,
    SubscriberStatus,
    Subscription,
    Recharge,
    PaymentMethod,
    PaymentStatus,
    UsageRecord,
    Complaint,
    ComplaintCategory,
    ComplaintStatus,
    ComplaintChannel,
    generate_deduplication_hash,
    PlanChange,
)


def test_create_telecom_circle_and_unique_constraint(db):
    """Test circle creation and unique code constraint."""
    circle = TelecomCircle(code="GJ_TEST", name="Gujarat Test", state="Gujarat")
    db.add(circle)
    db.commit()
    assert circle.id is not None

    # Duplicate code should raise IntegrityError
    dup_circle = TelecomCircle(code="GJ_TEST", name="Another Gujarat", state="Gujarat")
    db.add(dup_circle)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_user_creation_and_unique_email(db):
    """Test user creation and unique email constraint."""
    user = User(
        email="test_user@example.com",
        full_name="Test User",
        hashed_password="hashed_pw_xyz",
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    assert user.id is not None

    dup_user = User(
        email="test_user@example.com",
        full_name="Duplicate User",
        hashed_password="hashed_pw_abc",
    )
    db.add(dup_user)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_plan_creation_and_attributes(db):
    """Test plan entity with Decimal price, MB allowance, and validity."""
    circle = TelecomCircle(code="AHM_PLN", name="Ahmedabad Plan Circle", state="Gujarat")
    db.add(circle)
    db.commit()

    plan = Plan(
        code="TC-TST-299",
        name="Test Plan 299",
        circle_id=circle.id,
        price=Decimal("299.00"),
        validity_days=28,
        data_allowance_mb=2048,
        is_unlimited_data=False,
        talktime_minutes=-1,
        is_unlimited_calls=True,
        sms_count=100,
        plan_type=PlanType.DAILY_DATA,
    )
    db.add(plan)
    db.commit()

    assert plan.id is not None
    assert plan.price == Decimal("299.00")
    assert plan.circle.code == "AHM_PLN"


def test_subscriber_and_relationships(db):
    """Test subscriber creation, status, and relationships to user and circle."""
    circle = TelecomCircle(code="GJ_SUB", name="Gujarat Sub Circle", state="Gujarat")
    user = User(
        email="sub_user@example.com",
        full_name="Sub User",
        hashed_password="hashed_pw_xyz",
        role=UserRole.SUBSCRIBER,
    )
    db.add_all([circle, user])
    db.commit()

    subscriber = Subscriber(
        user_id=user.id,
        circle_id=circle.id,
        mobile_number="9898012345",
        full_name="Sub User",
        email="sub_user@example.com",
        status=SubscriberStatus.ACTIVE,
        sim_card_number="8991009999999999999",
    )
    db.add(subscriber)
    db.commit()

    assert subscriber.id is not None
    assert subscriber.user.email == "sub_user@example.com"
    assert subscriber.circle.code == "GJ_SUB"
    assert user.subscriber.id == subscriber.id

    # Unique mobile number constraint
    dup_sub = Subscriber(
        circle_id=circle.id,
        mobile_number="9898012345",
        full_name="Other User",
        sim_card_number="8991008888888888888",
    )
    db.add(dup_sub)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_subscription_and_recharge(db):
    """Test subscription and recharge transaction models with Decimal amounts."""
    circle = TelecomCircle(code="GJ_TXN", name="Gujarat Txn", state="Gujarat")
    db.add(circle)
    db.commit()

    plan = Plan(
        code="TC-TXN-199",
        name="Txn Plan 199",
        circle_id=circle.id,
        price=Decimal("199.00"),
        validity_days=28,
        data_allowance_mb=1536,
    )
    subscriber = Subscriber(
        circle_id=circle.id,
        mobile_number="9879012345",
        full_name="Txn Subscriber",
        sim_card_number="8991007777777777777",
    )
    db.add_all([plan, subscriber])
    db.commit()

    now = datetime.now(timezone.utc)
    subscription = Subscription(
        subscriber_id=subscriber.id,
        plan_id=plan.id,
        start_date=now,
        end_date=now + timedelta(days=28),
        is_active=True,
    )
    recharge = Recharge(
        transaction_id="TXN-TST-1001",
        subscriber_id=subscriber.id,
        plan_id=plan.id,
        amount=Decimal("199.00"),
        payment_method=PaymentMethod.UPI,
        payment_status=PaymentStatus.SUCCESS,
    )
    db.add_all([subscription, recharge])
    db.commit()

    assert subscription.id is not None
    assert subscription.plan.code == "TC-TXN-199"
    assert recharge.id is not None
    assert recharge.amount == Decimal("199.00")
    assert recharge.subscriber.mobile_number == "9879012345"


def test_usage_record(db):
    """Test usage records stored consistently in MB."""
    circle = TelecomCircle(code="GJ_USG", name="Gujarat Usage", state="Gujarat")
    db.add(circle)
    db.commit()

    subscriber = Subscriber(
        circle_id=circle.id,
        mobile_number="9879123456",
        full_name="Usage Sub",
        sim_card_number="8991006666666666666",
    )
    db.add(subscriber)
    db.commit()

    usage = UsageRecord(
        subscriber_id=subscriber.id,
        data_used_mb=Decimal("1536.50"),
        call_duration_seconds=360,
        sms_sent=2,
    )
    db.add(usage)
    db.commit()

    assert usage.id is not None
    assert usage.data_used_mb == Decimal("1536.50")
    assert usage.subscriber.id == subscriber.id


def test_complaint_and_deduplication_hash(db):
    """Test complaint creation, resolution, and deduplication hash generation."""
    circle = TelecomCircle(code="GJ_CMP", name="Gujarat Complaint", state="Gujarat")
    db.add(circle)
    db.commit()

    subscriber = Subscriber(
        circle_id=circle.id,
        mobile_number="9879234567",
        full_name="Complaint Sub",
        sim_card_number="8991005555555555555",
    )
    db.add(subscriber)
    db.commit()

    entry_date = date(2026, 11, 6)
    hash_1 = generate_deduplication_hash(
        subscriber_id=subscriber.id,
        category="NETWORK",
        subject="No 5G signal in Navrangpura",
        entry_date=entry_date,
    )
    # Extra whitespace and different casing should generate exact same hash
    hash_2 = generate_deduplication_hash(
        subscriber_id=subscriber.id,
        category="NETWORK",
        subject="   no 5g   signal in NAVRANGPURA  ",
        entry_date=entry_date,
    )
    assert hash_1 == hash_2

    complaint = Complaint(
        ticket_number="CMP-TST-001",
        subscriber_id=subscriber.id,
        category=ComplaintCategory.NETWORK,
        subject="No 5G signal in Navrangpura",
        description="Detailed description of network issue",
        channel=ComplaintChannel.APP,
        status=ComplaintStatus.OPEN,
        deduplication_hash=hash_1,
    )
    db.add(complaint)
    db.commit()

    assert complaint.id is not None
    assert complaint.ticket_number == "CMP-TST-001"
    assert complaint.subscriber.id == subscriber.id


def test_plan_change_history(db):
    """Test plan change record linking old plan, new plan, and user."""
    circle = TelecomCircle(code="GJ_PC", name="Gujarat PC", state="Gujarat")
    user = User(
        email="agent@example.com",
        full_name="Agent Sharma",
        hashed_password="pw",
        role=UserRole.STAFF,
    )
    db.add_all([circle, user])
    db.commit()

    p1 = Plan(
        code="TC-PC-1",
        name="Plan 1",
        circle_id=circle.id,
        price=Decimal("199.00"),
        validity_days=28,
        data_allowance_mb=1024,
    )
    p2 = Plan(
        code="TC-PC-2",
        name="Plan 2",
        circle_id=circle.id,
        price=Decimal("299.00"),
        validity_days=28,
        data_allowance_mb=2048,
    )
    sub = Subscriber(
        circle_id=circle.id,
        mobile_number="9879345678",
        full_name="Plan Change Sub",
        sim_card_number="8991004444444444444",
    )
    db.add_all([p1, p2, sub])
    db.commit()

    pc = PlanChange(
        subscriber_id=sub.id,
        old_plan_id=p1.id,
        new_plan_id=p2.id,
        reason="Upgraded for higher data allowance",
        changed_by_user_id=user.id,
    )
    db.add(pc)
    db.commit()

    assert pc.id is not None
    assert pc.old_plan.code == "TC-PC-1"
    assert pc.new_plan.code == "TC-PC-2"
    assert pc.changed_by_user.email == "agent@example.com"
