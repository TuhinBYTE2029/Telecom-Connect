"""Integration tests for Data/Voice/SMS Usage API endpoints."""
from fastapi.testclient import TestClient


def create_usage_fixtures(client: TestClient):
    """Helper to create circle and subscriber for usage tests."""
    c_resp = client.post(
        "/api/v1/circles/",
        json={"code": "USG_CIR", "name": "Usage Circle", "state": "Gujarat"},
    )
    circle_id = c_resp.json()["id"]

    s_resp = client.post(
        "/api/v1/subscribers/",
        json={
            "circle_id": circle_id,
            "mobile_number": "9825900003",
            "full_name": "Usage Tester",
            "sim_card_number": "8991009000030000003",
            "status": "active",
        },
    )
    subscriber_id = s_resp.json()["id"]
    return subscriber_id


def test_record_data_usage_and_computed_gb(client: TestClient):
    """Test recording data usage and verifying computed data_used_gb field."""
    sub_id = create_usage_fixtures(client)

    payload = {
        "subscriber_id": sub_id,
        "data_used_mb": 2048.00,  # 2 GB
        "call_duration_seconds": 0,
        "sms_sent": 0,
    }
    response = client.post("/api/v1/usage/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data_used_mb"] == "2048.00"
    assert data["data_used_gb"] == 2.0
    assert data["usage_type"] == "DATA"


def test_record_voice_and_sms_usage(client: TestClient):
    """Test recording call duration and SMS."""
    sub_id = create_usage_fixtures(client)

    payload = {
        "subscriber_id": sub_id,
        "data_used_mb": 0.00,
        "call_duration_seconds": 300,
        "sms_sent": 5,
    }
    response = client.post("/api/v1/usage/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["call_duration_seconds"] == 300
    assert data["sms_sent"] == 5
    assert data["usage_type"] in ["VOICE", "SMS", "MIXED"]


def test_record_usage_invalid_all_zero(client: TestClient):
    """Test that all-zero usage values raise 400 Bad Request."""
    sub_id = create_usage_fixtures(client)

    payload = {
        "subscriber_id": sub_id,
        "data_used_mb": 0.00,
        "call_duration_seconds": 0,
        "sms_sent": 0,
    }
    response = client.post("/api/v1/usage/", json=payload)
    assert response.status_code == 400
    assert "at least one usage metric" in response.json()["error"]["message"].lower()


def test_get_subscriber_usage_and_summary(client: TestClient):
    """Test retrieving usage list and aggregated usage summary."""
    sub_id = create_usage_fixtures(client)

    # Record 2 entries
    client.post(
        "/api/v1/usage/",
        json={"subscriber_id": sub_id, "data_used_mb": 1024.00, "call_duration_seconds": 60, "sms_sent": 2},
    )
    client.post(
        "/api/v1/usage/",
        json={"subscriber_id": sub_id, "data_used_mb": 2048.00, "call_duration_seconds": 120, "sms_sent": 1},
    )

    # 1. List usage
    list_resp = client.get(f"/api/v1/usage/{sub_id}")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 2

    # 2. Summary
    sum_resp = client.get(f"/api/v1/usage/summary/{sub_id}")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["subscriber_id"] == sub_id
    assert float(summary["total_data_used_mb"]) >= 3072.00
    assert summary["total_data_used_gb"] >= 3.0
    assert summary["total_call_duration_seconds"] >= 180
    assert summary["total_call_duration_minutes"] >= 3.0
    assert summary["total_sms_sent"] >= 3


def test_usage_missing_subscriber(client: TestClient):
    """Test 404 response for missing subscriber."""
    response = client.get("/api/v1/usage/summary/999999")
    assert response.status_code == 404
