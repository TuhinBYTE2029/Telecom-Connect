"""Integration tests for Recharge API endpoints and subscription updates."""
from fastapi.testclient import TestClient


def create_test_fixtures(client: TestClient):
    """Helper fixture creating a circle, plan, and active subscriber."""
    c_resp = client.post(
        "/api/v1/circles/",
        json={"code": "RC_CIR", "name": "Recharge Circle", "state": "Gujarat"},
    )
    circle_id = c_resp.json()["id"]

    p_resp = client.post(
        "/api/v1/plans/",
        json={
            "code": "TC-RC-299",
            "name": "Recharge Plan 299",
            "price": 299.00,
            "validity_days": 28,
            "data_allowance_mb": 2048,
        },
    )
    plan_id = p_resp.json()["id"]

    s_resp = client.post(
        "/api/v1/subscribers/",
        json={
            "circle_id": circle_id,
            "mobile_number": "9825900001",
            "full_name": "Recharge Tester",
            "sim_card_number": "8991009000010000001",
            "status": "active",
        },
    )
    subscriber_id = s_resp.json()["id"]

    return circle_id, plan_id, subscriber_id


def test_create_recharge_success_and_subscription_activation(client: TestClient):
    """Test successful recharge creation, transaction ID generation, and subscription creation."""
    _, plan_id, subscriber_id = create_test_fixtures(client)

    payload = {
        "subscriber_id": subscriber_id,
        "plan_id": plan_id,
        "amount": 299.00,
        "payment_method": "UPI",
    }
    response = client.post("/api/v1/recharges", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["payment_status"] == "SUCCESS"
    assert data["amount"] == "299.00"
    assert data["transaction_id"].startswith("TXN-")
    assert data["subscriber_id"] == subscriber_id


def test_create_recharge_simulated_failure(client: TestClient):
    """Test payment simulation failure recording status FAILED without activating subscription."""
    _, plan_id, subscriber_id = create_test_fixtures(client)

    payload = {
        "subscriber_id": subscriber_id,
        "plan_id": plan_id,
        "amount": 299.00,
        "payment_method": "CREDIT_CARD",
        "simulate_failure": True,
        "failure_reason": "Card expired / insufficient limit",
    }
    response = client.post("/api/v1/recharges", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["payment_status"] == "FAILED"
    assert data["failure_reason"] == "Card expired / insufficient limit"


def test_recharge_invalid_amount(client: TestClient):
    """Test that recharge amount mismatching plan price raises 400 Bad Request."""
    _, plan_id, subscriber_id = create_test_fixtures(client)

    payload = {
        "subscriber_id": subscriber_id,
        "plan_id": plan_id,
        "amount": 100.00,  # Plan price is 299.00
    }
    response = client.post("/api/v1/recharges", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
    assert "does not match plan price" in response.json()["error"]["message"].lower()


def test_recharge_ineligible_subscriber(client: TestClient):
    """Test that ported-out subscriber cannot be recharged."""
    circle_resp = client.post(
        "/api/v1/circles/",
        json={"code": "INEL", "name": "Ineligible Circle", "state": "Gujarat"},
    )
    c_id = circle_resp.json()["id"]

    p_resp = client.post(
        "/api/v1/plans/",
        json={
            "code": "TC-INEL-199",
            "name": "Ineligible Plan",
            "price": 199.00,
            "validity_days": 28,
            "data_allowance_mb": 1024,
        },
    )
    p_id = p_resp.json()["id"]

    s_resp = client.post(
        "/api/v1/subscribers/",
        json={
            "circle_id": c_id,
            "mobile_number": "9825900002",
            "full_name": "Ported Out Sub",
            "sim_card_number": "8991009000020000002",
            "status": "ported_out",
        },
    )
    s_id = s_resp.json()["id"]

    response = client.post(
        "/api/v1/recharges",
        json={"subscriber_id": s_id, "plan_id": p_id},
    )
    assert response.status_code == 400
    assert "ported-out subscribers cannot be recharged" in response.json()["error"]["message"].lower()


def test_list_recharges_and_subscriber_history(client: TestClient):
    """Test listing all recharges and querying subscriber recharge history."""
    _, plan_id, subscriber_id = create_test_fixtures(client)

    # Perform a recharge
    client.post(
        "/api/v1/recharges",
        json={"subscriber_id": subscriber_id, "plan_id": plan_id},
    )

    # 1. Global list
    resp1 = client.get("/api/v1/recharges?page=1&page_size=10")
    assert resp1.status_code == 200
    assert resp1.json()["total"] >= 1

    # 2. Subscriber specific history
    resp2 = client.get(f"/api/v1/subscribers/{subscriber_id}/recharges")
    assert resp2.status_code == 200
    assert resp2.json()["total"] >= 1
    assert resp2.json()["items"][0]["subscriber_id"] == subscriber_id


def test_get_recharge_by_id(client: TestClient):
    """Test retrieving recharge by transaction primary key ID."""
    _, plan_id, subscriber_id = create_test_fixtures(client)
    rc_resp = client.post(
        "/api/v1/recharges",
        json={"subscriber_id": subscriber_id, "plan_id": plan_id},
    )
    rc_id = rc_resp.json()["id"]

    get_resp = client.get(f"/api/v1/recharges/{rc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == rc_id

    # 404 for missing
    missing_resp = client.get("/api/v1/recharges/999999")
    assert missing_resp.status_code == 404
