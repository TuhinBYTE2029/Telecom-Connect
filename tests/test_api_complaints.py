"""Integration tests for Complaint API and cross-channel deduplication."""
from fastapi.testclient import TestClient


def create_complaint_fixtures(client: TestClient):
    """Helper creating circle and subscriber for complaint tests."""
    c_resp = client.post(
        "/api/v1/circles/",
        json={"code": "CMP_CIR", "name": "Complaint Circle", "state": "Gujarat"},
    )
    circle_id = c_resp.json()["id"]

    s_resp = client.post(
        "/api/v1/subscribers/",
        json={
            "circle_id": circle_id,
            "mobile_number": "9825900004",
            "full_name": "Complaint Tester",
            "sim_card_number": "8991009000040000004",
            "status": "active",
        },
    )
    return s_resp.json()["id"]


def test_create_complaint_and_cross_channel_deduplication(client: TestClient):
    """Test complaint creation and cross-channel duplicate detection."""
    sub_id = create_complaint_fixtures(client)

    # 1. First complaint submitted via APP
    payload_app = {
        "subscriber_id": sub_id,
        "category": "NETWORK",
        "subject": "5G network tower down in Navrangpura",
        "description": "Call drops and internet connectivity lost since morning.",
        "channel": "APP",
    }
    resp1 = client.post("/api/v1/complaints/", json=payload_app)
    assert resp1.status_code == 201
    ticket = resp1.json()["ticket_number"]
    assert ticket.startswith("CMP-")
    assert resp1.json()["status"] == "OPEN"

    # 2. Duplicate complaint for same issue submitted via CALL_CENTER
    payload_call_center = {
        "subscriber_id": sub_id,
        "category": "NETWORK",
        "subject": "  5G network tower DOWN in   Navrangpura  ",  # Normalized matching
        "description": "User phoned in complaining about the same tower outage.",
        "channel": "CALL_CENTER",
    }
    resp2 = client.post("/api/v1/complaints/", json=payload_call_center)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"
    assert "duplicate complaint detected" in resp2.json()["error"]["message"].lower()

    # 3. Unrelated complaint for same subscriber under different category -> Should succeed!
    payload_billing = {
        "subscriber_id": sub_id,
        "category": "BILLING",
        "subject": "Incorrect tax computation on invoice",
        "description": "Discrepancy in GST calculation on last recharge.",
        "channel": "WEB",
    }
    resp3 = client.post("/api/v1/complaints/", json=payload_billing)
    assert resp3.status_code == 201
    assert resp3.json()["category"] == "BILLING"


def test_list_and_patch_complaint(client: TestClient):
    """Test listing complaints with filters and patching complaint status and staff."""
    sub_id = create_complaint_fixtures(client)

    # Create complaint
    create_resp = client.post(
        "/api/v1/complaints/",
        json={
            "subscriber_id": sub_id,
            "category": "SERVICE",
            "subject": "SIM card e-SIM profile transfer delayed",
            "description": "eSIM activation QR code not delivered to email.",
            "channel": "APP",
        },
    )
    cmp_id = create_resp.json()["id"]

    # List complaints
    list_resp = client.get("/api/v1/complaints/?category=SERVICE")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # Patch complaint to IN_PROGRESS
    patch_resp1 = client.patch(
        f"/api/v1/complaints/{cmp_id}",
        json={"status": "IN_PROGRESS", "resolution_notes": "Assigned to network engineer"},
    )
    assert patch_resp1.status_code == 200
    assert patch_resp1.json()["status"] == "IN_PROGRESS"
    assert patch_resp1.json()["resolved_at"] is None

    # Patch complaint to RESOLVED
    patch_resp2 = client.patch(
        f"/api/v1/complaints/{cmp_id}",
        json={"status": "RESOLVED", "resolution_notes": "eSIM profile re-sent successfully"},
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["status"] == "RESOLVED"
    assert patch_resp2.json()["resolved_at"] is not None


def test_get_complaint_not_found(client: TestClient):
    """Test 404 for missing complaint ID."""
    response = client.get("/api/v1/complaints/999999")
    assert response.status_code == 404
