"""Database seed script with realistic fictional Ahmedabad/Gujarat telecom data.

Safe to execute multiple times (idempotent).
"""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import bcrypt

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
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


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def seed_database() -> None:
    init_db()
    db = SessionLocal()
    try:
        print("[*] Seeding Telecom Connect database...")

        # 1. Telecom Circles
        circles_data = [
            {"code": "GJ", "name": "Gujarat Telecom Circle", "state": "Gujarat"},
            {"code": "AHM", "name": "Ahmedabad Metro Circle", "state": "Gujarat"},
            {"code": "MH", "name": "Maharashtra & Goa Circle", "state": "Maharashtra"},
            {"code": "DL", "name": "Delhi NCR Circle", "state": "Delhi"},
            {"code": "KA", "name": "Karnataka Circle", "state": "Karnataka"},
        ]
        circles = {}
        for c in circles_data:
            circle = db.query(TelecomCircle).filter_by(code=c["code"]).first()
            if not circle:
                circle = TelecomCircle(
                    code=c["code"],
                    name=c["name"],
                    state=c["state"],
                    is_active=True,
                )
                db.add(circle)
                db.flush()
                print(f"  + Added Circle: {c['code']} - {c['name']}")
            circles[c["code"]] = circle

        # 2. Users (Admin, Staff, Subscribers)
        admin_password_hash = hash_password("AdminSecure2026!")
        staff_password_hash = hash_password("StaffSecure2026!")
        user_password_hash = hash_password("UserPass2026!")

        users_data = [
            {
                "email": "admin@telecomconnect.in",
                "full_name": "Admin Ahmedabad",
                "role": UserRole.ADMIN,
                "hashed_password": admin_password_hash,
            },
            {
                "email": "staff.ahmedabad@telecomconnect.in",
                "full_name": "Kavita Joshi",
                "role": UserRole.STAFF,
                "hashed_password": staff_password_hash,
            },
            {
                "email": "aarav.patel@example.com",
                "full_name": "Aarav Patel",
                "role": UserRole.SUBSCRIBER,
                "hashed_password": user_password_hash,
            },
            {
                "email": "diya.shah@example.com",
                "full_name": "Diya Shah",
                "role": UserRole.SUBSCRIBER,
                "hashed_password": user_password_hash,
            },
            {
                "email": "mehul.mehta@example.com",
                "full_name": "Mehul Mehta",
                "role": UserRole.SUBSCRIBER,
                "hashed_password": user_password_hash,
            },
        ]
        users = {}
        for u in users_data:
            user = db.query(User).filter_by(email=u["email"]).first()
            if not user:
                user = User(
                    email=u["email"],
                    full_name=u["full_name"],
                    role=u["role"],
                    hashed_password=u["hashed_password"],
                    is_active=True,
                )
                db.add(user)
                db.flush()
                print(f"  + Added User: {u['email']} ({u['role'].value})")
            users[u["email"]] = user

        # 3. Prepaid Plans
        plans_data = [
            {
                "code": "TC-GJ-199",
                "name": "Smart Connect 199",
                "circle_id": circles["GJ"].id,
                "price": Decimal("199.00"),
                "validity_days": 28,
                "data_allowance_mb": 1536,  # 1.5 GB/day
                "is_unlimited_data": False,
                "talktime_minutes": -1,
                "is_unlimited_calls": True,
                "sms_count": 100,
                "plan_type": PlanType.DAILY_DATA,
                "description": "Daily 1.5GB 4G/5G data with unlimited calls across India.",
            },
            {
                "code": "TC-AHM-299",
                "name": "Ahmedabad Super Connect 299",
                "circle_id": circles["AHM"].id,
                "price": Decimal("299.00"),
                "validity_days": 28,
                "data_allowance_mb": 2048,  # 2 GB/day
                "is_unlimited_data": False,
                "talktime_minutes": -1,
                "is_unlimited_calls": True,
                "sms_count": 100,
                "plan_type": PlanType.DAILY_DATA,
                "description": "Daily 2GB data + unlimited 5G in Ahmedabad Metro Circle.",
            },
            {
                "code": "TC-GJ-499",
                "name": "Gujarat Freedom 499",
                "circle_id": circles["GJ"].id,
                "price": Decimal("499.00"),
                "validity_days": 56,
                "data_allowance_mb": 2048,
                "is_unlimited_data": False,
                "talktime_minutes": -1,
                "is_unlimited_calls": True,
                "sms_count": 100,
                "plan_type": PlanType.DAILY_DATA,
                "description": "56-day pack with 2GB daily data and unlimited calling.",
            },
            {
                "code": "TC-GJ-666",
                "name": "Cricket Dhamaka 666",
                "circle_id": circles["GJ"].id,
                "price": Decimal("666.00"),
                "validity_days": 84,
                "data_allowance_mb": 1536,
                "is_unlimited_data": False,
                "talktime_minutes": -1,
                "is_unlimited_calls": True,
                "sms_count": 100,
                "plan_type": PlanType.DAILY_DATA,
                "description": "84-day cricket streaming pack with high-speed 1.5GB/day data.",
            },
            {
                "code": "TC-NAT-2999",
                "name": "All-India Annual Pro 2999",
                "circle_id": None,  # All-India
                "price": Decimal("2999.00"),
                "validity_days": 365,
                "data_allowance_mb": 2560,  # 2.5 GB/day
                "is_unlimited_data": False,
                "talktime_minutes": -1,
                "is_unlimited_calls": True,
                "sms_count": 100,
                "plan_type": PlanType.ANNUAL,
                "description": "Annual 365-day plan with 2.5GB daily data and unlimited roaming.",
            },
            {
                "code": "TC-BOOST-61",
                "name": "Data Booster 6GB",
                "circle_id": None,
                "price": Decimal("61.00"),
                "validity_days": 28,
                "data_allowance_mb": 6144,  # 6 GB lump sum
                "is_unlimited_data": False,
                "talktime_minutes": 0,
                "is_unlimited_calls": False,
                "sms_count": 0,
                "plan_type": PlanType.DATA_BOOSTER,
                "description": "6GB instant high-speed data booster valid with base pack.",
            },
        ]
        plans = {}
        for p in plans_data:
            plan = db.query(Plan).filter_by(code=p["code"]).first()
            if not plan:
                plan = Plan(
                    code=p["code"],
                    name=p["name"],
                    circle_id=p["circle_id"],
                    price=p["price"],
                    validity_days=p["validity_days"],
                    data_allowance_mb=p["data_allowance_mb"],
                    is_unlimited_data=p["is_unlimited_data"],
                    talktime_minutes=p["talktime_minutes"],
                    is_unlimited_calls=p["is_unlimited_calls"],
                    sms_count=p["sms_count"],
                    plan_type=p["plan_type"],
                    description=p["description"],
                    is_active=True,
                )
                db.add(plan)
                db.flush()
                print(f"  + Added Plan: {p['code']} (INR {p['price']})")
            plans[p["code"]] = plan

        # 4. Subscribers
        subscribers_data = [
            {
                "user_id": users["aarav.patel@example.com"].id,
                "circle_id": circles["AHM"].id,
                "mobile_number": "9825012345",
                "full_name": "Aarav Patel",
                "email": "aarav.patel@example.com",
                "status": SubscriberStatus.ACTIVE,
                "sim_card_number": "8991001234567890123",
            },
            {
                "user_id": users["diya.shah@example.com"].id,
                "circle_id": circles["AHM"].id,
                "mobile_number": "9825123456",
                "full_name": "Diya Shah",
                "email": "diya.shah@example.com",
                "status": SubscriberStatus.ACTIVE,
                "sim_card_number": "8991001234567890124",
            },
            {
                "user_id": users["mehul.mehta@example.com"].id,
                "circle_id": circles["GJ"].id,
                "mobile_number": "9825234567",
                "full_name": "Mehul Mehta",
                "email": "mehul.mehta@example.com",
                "status": SubscriberStatus.ACTIVE,
                "sim_card_number": "8991001234567890125",
            },
            {
                "user_id": None,
                "circle_id": circles["GJ"].id,
                "mobile_number": "9825345678",
                "full_name": "Ritu Trivedi",
                "email": "ritu.trivedi@example.com",
                "status": SubscriberStatus.SUSPENDED,
                "sim_card_number": "8991001234567890126",
            },
            {
                "user_id": None,
                "circle_id": circles["GJ"].id,
                "mobile_number": "9825456789",
                "full_name": "Jatin Dave",
                "email": "jatin.dave@example.com",
                "status": SubscriberStatus.PORTED_OUT,
                "sim_card_number": "8991001234567890127",
            },
        ]
        subscribers = {}
        now = datetime.now(timezone.utc)
        for s in subscribers_data:
            sub = db.query(Subscriber).filter_by(mobile_number=s["mobile_number"]).first()
            if not sub:
                sub = Subscriber(
                    user_id=s["user_id"],
                    circle_id=s["circle_id"],
                    mobile_number=s["mobile_number"],
                    full_name=s["full_name"],
                    email=s["email"],
                    status=s["status"],
                    sim_card_number=s["sim_card_number"],
                    activation_date=now - timedelta(days=60),
                    ported_out_at=(
                        now - timedelta(days=5)
                        if s["status"] == SubscriberStatus.PORTED_OUT
                        else None
                    ),
                )
                db.add(sub)
                db.flush()
                print(f"  + Added Subscriber: {s['mobile_number']} ({s['status'].value})")
            subscribers[s["mobile_number"]] = sub

        # 5. Subscriptions
        for mobile, plan_code in [
            ("9825012345", "TC-AHM-299"),
            ("9825123456", "TC-GJ-199"),
            ("9825234567", "TC-GJ-499"),
        ]:
            sub = subscribers[mobile]
            pln = plans[plan_code]
            existing_sub = (
                db.query(Subscription)
                .filter_by(subscriber_id=sub.id, plan_id=pln.id, is_active=True)
                .first()
            )
            if not existing_sub:
                subscription = Subscription(
                    subscriber_id=sub.id,
                    plan_id=pln.id,
                    start_date=now - timedelta(days=10),
                    end_date=now + timedelta(days=pln.validity_days - 10),
                    is_active=True,
                    auto_renew=False,
                )
                db.add(subscription)
                db.flush()
                print(f"  + Added Active Subscription for {mobile} on {plan_code}")

        # 6. Recharge Transactions
        recharges_data = [
            {
                "txn": "TXN-20261101-0001",
                "mobile": "9825012345",
                "plan": "TC-AHM-299",
                "amount": Decimal("299.00"),
                "method": PaymentMethod.UPI,
                "status": PaymentStatus.SUCCESS,
                "time": now - timedelta(days=10),
                "reason": None,
            },
            {
                "txn": "TXN-20261102-0002",
                "mobile": "9825123456",
                "plan": "TC-GJ-199",
                "amount": Decimal("199.00"),
                "method": PaymentMethod.NET_BANKING,
                "status": PaymentStatus.SUCCESS,
                "time": now - timedelta(days=9),
                "reason": None,
            },
            {
                "txn": "TXN-20261103-0003",
                "mobile": "9825012345",
                "plan": "TC-BOOST-61",
                "amount": Decimal("61.00"),
                "method": PaymentMethod.UPI,
                "status": PaymentStatus.FAILED,
                "time": now - timedelta(days=2),
                "reason": "Payment declined by customer bank (insufficient balance)",
            },
        ]
        for r in recharges_data:
            existing_rc = db.query(Recharge).filter_by(transaction_id=r["txn"]).first()
            if not existing_rc:
                rc = Recharge(
                    transaction_id=r["txn"],
                    subscriber_id=subscribers[r["mobile"]].id,
                    plan_id=plans[r["plan"]].id,
                    amount=r["amount"],
                    payment_method=r["method"],
                    payment_status=r["status"],
                    failure_reason=r["reason"],
                    transaction_time=r["time"],
                )
                db.add(rc)
                db.flush()
                print(f"  + Added Recharge: {r['txn']} ({r['status'].value})")

        # 7. Usage Records
        for mobile in ["9825012345", "9825123456"]:
            sub = subscribers[mobile]
            has_records = db.query(UsageRecord).filter_by(subscriber_id=sub.id).count()
            if has_records == 0:
                for d in range(1, 4):
                    ur = UsageRecord(
                        subscriber_id=sub.id,
                        record_timestamp=now - timedelta(days=d),
                        data_used_mb=Decimal(f"{1120.50 + d * 150.25:.2f}"),
                        call_duration_seconds=1200 + d * 300,
                        sms_sent=3 + d,
                    )
                    db.add(ur)
                print(f"  + Added Usage Records for {mobile}")

        # 8. Complaints
        complaints_data = [
            {
                "ticket": "CMP-20261104-001",
                "mobile": "9825012345",
                "category": ComplaintCategory.NETWORK,
                "subject": "Intermittent 5G coverage near Navrangpura Ahmedabad",
                "description": "5G network drops to 3G during evening peak hours around Gujarat University area.",
                "channel": ComplaintChannel.APP,
                "status": ComplaintStatus.IN_PROGRESS,
            },
            {
                "ticket": "CMP-20261105-002",
                "mobile": "9825123456",
                "category": ComplaintCategory.BILLING,
                "subject": "Data deduction discrepancy after video stream",
                "description": "Observed 300MB extra data deduction on account during afternoon.",
                "channel": ComplaintChannel.CALL_CENTER,
                "status": ComplaintStatus.RESOLVED,
            },
        ]
        for cmp_data in complaints_data:
            existing_cmp = db.query(Complaint).filter_by(ticket_number=cmp_data["ticket"]).first()
            if not existing_cmp:
                sub = subscribers[cmp_data["mobile"]]
                hash_val = generate_deduplication_hash(
                    subscriber_id=sub.id,
                    category=cmp_data["category"].value,
                    subject=cmp_data["subject"],
                    entry_date=date.today(),
                )
                cmp = Complaint(
                    ticket_number=cmp_data["ticket"],
                    subscriber_id=sub.id,
                    category=cmp_data["category"],
                    subject=cmp_data["subject"],
                    description=cmp_data["description"],
                    channel=cmp_data["channel"],
                    status=cmp_data["status"],
                    deduplication_hash=hash_val,
                    resolution_notes=(
                        "Issue resolved with network tower optimization."
                        if cmp_data["status"] == ComplaintStatus.RESOLVED
                        else None
                    ),
                    resolved_at=(
                        now - timedelta(hours=6)
                        if cmp_data["status"] == ComplaintStatus.RESOLVED
                        else None
                    ),
                )
                db.add(cmp)
                print(f"  + Added Complaint: {cmp_data['ticket']} ({cmp_data['status'].value})")

        # 9. Plan Changes
        sub_aarav = subscribers["9825012345"]
        has_pc = db.query(PlanChange).filter_by(subscriber_id=sub_aarav.id).count()
        if has_pc == 0:
            pc = PlanChange(
                subscriber_id=sub_aarav.id,
                old_plan_id=plans["TC-GJ-199"].id,
                new_plan_id=plans["TC-AHM-299"].id,
                reason="Upgraded to Ahmedabad Metro 2GB plan with 5G speed",
                changed_by_user_id=users["admin@telecomconnect.in"].id,
                effective_date=now - timedelta(days=10),
            )
            db.add(pc)
            print(f"  + Added PlanChange history for Aarav Patel")

        db.commit()
        print("[SUCCESS] Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during database seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
