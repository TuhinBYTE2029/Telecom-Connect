"""Unit tests verifying database seeding behavior and idempotency."""
from scripts.seed_data import seed_database
from app.models import (
    TelecomCircle,
    Plan,
    Subscriber,
    User,
    Subscription,
    Recharge,
    UsageRecord,
    Complaint,
    PlanChange,
)


def test_seed_database_idempotent(db):
    """Verify seed_database populates all entities and can be safely re-run without duplicate errors."""
    # First run
    seed_database()

    circles_count_1 = db.query(TelecomCircle).count()
    plans_count_1 = db.query(Plan).count()
    users_count_1 = db.query(User).count()
    subscribers_count_1 = db.query(Subscriber).count()
    recharges_count_1 = db.query(Recharge).count()
    complaints_count_1 = db.query(Complaint).count()

    assert circles_count_1 >= 5
    assert plans_count_1 >= 6
    assert users_count_1 >= 5
    assert subscribers_count_1 >= 5
    assert recharges_count_1 >= 3
    assert complaints_count_1 >= 2

    # Second run should succeed without error and without duplicating counts
    seed_database()

    assert db.query(TelecomCircle).count() == circles_count_1
    assert db.query(Plan).count() == plans_count_1
    assert db.query(Subscriber).count() == subscribers_count_1
    assert db.query(Recharge).count() == recharges_count_1
    assert db.query(Complaint).count() == complaints_count_1
