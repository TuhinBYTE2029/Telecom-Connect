"""Domain enumerations for Telecom Connect."""
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    SUBSCRIBER = "subscriber"


class SubscriberStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PORTED_OUT = "ported_out"


class PlanType(str, Enum):
    DAILY_DATA = "DAILY_DATA"
    UNLIMITED = "UNLIMITED"
    DATA_BOOSTER = "DATA_BOOSTER"
    TOP_UP = "TOP_UP"
    ANNUAL = "ANNUAL"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ComplaintCategory(str, Enum):
    NETWORK = "NETWORK"
    BILLING = "BILLING"
    RECHARGE = "RECHARGE"
    SERVICE = "SERVICE"
    PORTING = "PORTING"


class ComplaintStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class ComplaintChannel(str, Enum):
    APP = "APP"
    WEB = "WEB"
    CALL_CENTER = "CALL_CENTER"
    SMS = "SMS"
    STORE = "STORE"


class PlanChangeStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
