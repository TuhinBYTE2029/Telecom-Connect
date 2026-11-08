"""Integration tests for PlanChange API endpoints and history tracking."""
from fastapi.testclient import TestClient


def create_plan_change_fixtures(client: TestClient):
    """Helper to create circle, 2 plans, and subscriber."""
    c_resp = client.post(
        "/api/v1/circles/",
        json={"code": "PC_CIR", "name": "Plan Change Circle", "state": "Gujarat"},
    )
    circle_id = c_resp.json()["id"]

    p1_resp = client.post(
        "/api/v1/plans/",
        json={
            "code": "TC-PC-OLD",
            "name": "Old Base Plan 199",
            "price": 199.00,
            "validity_days": 28,
            "data_allowance_mb": 1536,
        },
    )
    p1_id = p1_resp.json()["id"]

    p2_resp = client.post(
        "/api/v1/plans/",
        json={
            "code": "TC-PC-NEW",
            "name": "New Target Plan 299",
            "price": 299.00,
            "validity_days": 28,
            "data_allowance_mb": 2048,
        },
    )
    p2_id = p2_resp.json()["id"]

    s_resp = client.post(
        "/api/v1/subscribers/",
        json={
            "circle_id": circle_id,
            "mobile_number": "9825900005",
            "full_name": "Plan Change Tester",
            "sim_card_number": "8991009000050000005",
            "status": "active",
        },
    )
    sub_id = s_resp.json()["id"]

    # Initial recharge on old plan
    client.post(
        "/api/v1/recharges",
        json={"subscriber_id": sub_id, "plan_id": p1_id},
    )

    return sub_id, p1_id, p2_id


def test_request_plan_change_success_and_subscription_update(client: TestClient):
    """Test successful plan change and active subscription migration."""
    sub_id, p1_id, p2_id = create_plan_change_fixtures(client)

    payload = {
        "subscriber_id": sub_id,
        "new_plan_id": p2_id,
        "reason": "Upgraded for 5G speed boost",
        "status": "COMPLETED",
    }
    response = client.post("/api/v1/plan-changes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["subscriber_id"] == sub_id
    assert data["old_plan_id"] == p1_id
    assert data["new_plan_id"] == p2_id
    assert data["status"] == "COMPLETED"
    assert data["reason"] == "Upgraded for 5G speed boost"


def test_plan_change_same_plan_rejected(client: TestClient):
    """Test that requesting the plan the subscriber is already on raises 400 Bad Request."""
    sub_id, p1_id, _ = create_plan_change_fixtures(client)

    payload = {
        "subscriber_id": sub_id,
        "new_plan_id": p1_id,  # Already active on p1_id
    }
    response = client.post("/api/v1/plan-changes/", json=payload)
    assert response.status_code == 400
    assert "already actively enrolled" in response.json()["error"]["message"].lower()


def test_plan_change_duplicate_pending(client: TestClient):
    """Test preventing duplicate pending plan change requests."""
    sub_id, _, p2_id = create_plan_change_fixtures(client)

    payload = {
        "subscriber_id": sub_id,
        "new_plan_id": p2_id,
        "status": "PENDING",
    }
    resp1 = client.post("/api/v1/plan-changes/", json=payload)
    assert resp1.status_code == 201
    assert resp1.json()["status"] == "PENDING"

    # Second pending request for same plan -> Should fail with 409 Conflict
    resp2 = client.post("/api/v1/plan-changes/", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"


def test_list_plan_change_history_and_get_by_id(client: TestClient):
    """Test querying subscriber plan change history and retrieving specific record."""
    sub_id, _, p2_id = create_plan_change_fixtures(client)

    # Submit plan change
    create_resp = client.post(
        "/api/v1/plan-changes/",
        json={"subscriber_id": sub_id, "new_plan_id": p2_id, "reason": "History test"},
    )
    change_id = create_resp.json()["id"]

    # 1. Subscriber history
    hist_resp = client.get(f"/api/v1/plan-changes/{sub_id}")
    assert hist_resp.status_code == 200
    assert hist_resp.json()["total"] >= 1
    assert hist_resp.json()["items"][0]["new_plan_id"] == p2_id

    # 2. Get by record ID
    get_resp = client.get(f"/api/v1/plan-changes/record/{change_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == change_id
    assert get_resp.json()["new_plan"]["id"] == p2_id

    # 3. Missing record 404
    missing_resp = client.get("/api/v1/plan-changes/record/999999")
    assert missing_resp.status_code == 404
