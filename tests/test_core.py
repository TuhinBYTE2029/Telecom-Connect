"""Tests for core configurations, logging, and exception handling."""
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.exceptions import (
    AppException,
    NotFoundError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)
from app.core.logging import logger, SensitiveMaskingFormatter
import logging


def test_cors_origins_parsing():
    """Test string list parsing in CORS origins."""
    s = Settings(CORS_ORIGINS='["http://localhost:3000","http://localhost:8000"]')
    assert len(s.CORS_ORIGINS) == 2
    assert "http://localhost:3000" in s.CORS_ORIGINS

    s2 = Settings(CORS_ORIGINS="http://foo.com, http://bar.com")
    assert s2.CORS_ORIGINS == ["http://foo.com", "http://bar.com"]

    assert s.is_production is False


def test_sensitive_logging_masking():
    """Verify passwords and tokens are redacted by logging formatter."""
    formatter = SensitiveMaskingFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='User login with password="super_secret_123" and token="jwt.abc.xyz"',
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "super_secret_123" not in formatted
    assert "jwt.abc.xyz" not in formatted
    assert "***REDACTED***" in formatted


def test_custom_exception_responses(client: TestClient):
    """Test custom exception responses when raised in app routes."""
    # Temporarily attach test route
    app = client.app

    @app.get("/test-not-found")
    def route_not_found():
        raise NotFoundError("Entity does not exist", details={"id": 42})

    @app.get("/test-bad-request")
    def route_bad_request():
        raise BadRequestError("Invalid payload")

    @app.get("/test-conflict")
    def route_conflict():
        raise ConflictError("Duplicate mobile number")

    resp1 = client.get("/test-not-found")
    assert resp1.status_code == 404
    data1 = resp1.json()
    assert data1["success"] is False
    assert data1["error"]["code"] == "NOT_FOUND"
    assert data1["error"]["details"] == {"id": 42}

    resp2 = client.get("/test-bad-request")
    assert resp2.status_code == 400
    assert resp2.json()["error"]["code"] == "BAD_REQUEST"

    resp3 = client.get("/test-conflict")
    assert resp3.status_code == 409
    assert resp3.json()["error"]["code"] == "CONFLICT"
