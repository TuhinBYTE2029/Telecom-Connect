"""Tests for configuration, health check, and root endpoints."""
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.database import check_db_connection


def test_settings_loaded():
    """Verify application configuration loads default and environment settings."""
    assert settings.APP_NAME == "Telecom Connect"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert len(settings.CORS_ORIGINS) > 0


def test_db_connection_check():
    """Verify database connection ping returns True."""
    assert check_db_connection() is True


def test_root_endpoint(client: TestClient):
    """Verify root endpoint responds with metadata and 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Telecom Connect"
    assert data["city"] == "Ahmedabad"
    assert data["status"] == "operational"
    assert data["documentation"] == "/docs"


def test_health_endpoint(client: TestClient):
    """Verify health endpoint responds with database status and 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["database"] == "reachable"
    assert data["services"]["api"] == "operational"


def test_openapi_schema(client: TestClient):
    """Verify OpenAPI JSON docs generation."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Telecom Connect"
