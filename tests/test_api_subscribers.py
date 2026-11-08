"""Integration tests for Subscribers REST API endpoints."""
from fastapi.testclient import TestClient


def get_or_create_circle(client: TestClient) -> int:
    """Helper to ensure a test circle exists."""
    resp = client.get("/api/v1/circles/?search=GJ_TEST_SUB")
    if resp.status_code == 200 and resp.json()["total"] > 0:
        return resp.json()["items"][0]["id"]
    create_resp = client.post(
        "/api/v1/circles/",
        json={
            "code": "GJSUB",
            "name": "Gujarat Subscriber Circle",
            "state": "Gujarat",
            "is_active": True,
        },
    )
    if create_resp.status_code == 201:
        return create_resp.json()["id"]
    # Fallback to listing first available circle
    list_resp = client.get("/api/v1/circles/")
    return list_resp.json()["items"][0]["id"]


def test_create_subscriber_success(client: TestClient):
    """Test creating a new subscriber with 10-digit mobile number."""
    circle_id = get_or_create_circle(client)
    payload = {
        "circle_id": circle_id,
        "mobile_number": "9898111222",
        "full_name": "Tushar Trivedi",
        "email": "tushar.trivedi@example.com",
        "sim_card_number": "8991001111222233334",
        "status": "active",
    }
    response = client.post("/api/v1/subscribers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mobile_number"] == "9898111222"
    assert data["status"] == "active"
    assert data["id"] is not None


def test_create_subscriber_duplicate_mobile_and_sim(client: TestClient):
    """Test duplicate mobile and SIM numbers raise 409 Conflict."""
    circle_id = get_or_create_circle(client)
    payload = {
        "circle_id": circle_id,
        "mobile_number": "9898222333",
        "full_name": "Kiran Patel",
        "sim_card_number": "8991002222333344445",
        "status": "active",
    }
    resp1 = client.post("/api/v1/subscribers/", json=payload)
    assert resp1.status_code == 201

    # Same mobile number
    dup_mobile_payload = {**payload, "sim_card_number": "8991009999888877776"}
    resp2 = client.post("/api/v1/subscribers/", json=dup_mobile_payload)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"

    # Same SIM card number
    dup_sim_payload = {**payload, "mobile_number": "9898333444"}
    resp3 = client.post("/api/v1/subscribers/", json=dup_sim_payload)
    assert resp3.status_code == 409
    assert resp3.json()["error"]["code"] == "CONFLICT"


def test_list_subscribers_search_and_filters(client: TestClient):
    """Test listing subscribers with search, status filters, and exclude_ported_out."""
    circle_id = get_or_create_circle(client)
    client.post(
        "/api/v1/subscribers/",
        json={
            "circle_id": circle_id,
            "mobile_number": "9898222333",
            "full_name": "Search Target",
            "sim_card_number": "8991008888777766665",
            "status": "active",
        },
    )

    response = client.get("/api/v1/subscribers/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

    # Search by mobile
    search_resp = client.get("/api/v1/subscribers/?search=9898222333")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert any(s["mobile_number"] == "9898222333" for s in search_data["items"])

    # Filter by status
    status_resp = client.get("/api/v1/subscribers/?status=active")
    assert status_resp.status_code == 200
    for s in status_resp.json()["items"]:
        assert s["status"] == "active"

    # Exclude ported out
    exclude_resp = client.get("/api/v1/subscribers/?exclude_ported_out=true")
    assert exclude_resp.status_code == 200
    for s in exclude_resp.json()["items"]:
        assert s["status"] != "ported_out"


def test_get_subscriber_by_id_and_by_mobile(client: TestClient):
    """Test lookup by subscriber ID and lookup by mobile number."""
    circle_id = get_or_create_circle(client)
    payload = {
        "circle_id": circle_id,
        "mobile_number": "9898444555",
        "full_name": "Pooja Vora",
        "sim_card_number": "8991004444555566667",
        "status": "active",
    }
    create_resp = client.post("/api/v1/subscribers/", json=payload)
    sub_id = create_resp.json()["id"]

    # Get by ID
    get_id_resp = client.get(f"/api/v1/subscribers/{sub_id}")
    assert get_id_resp.status_code == 200
    assert get_id_resp.json()["mobile_number"] == "9898444555"
    assert get_id_resp.json()["circle"] is not None

    # Get by Mobile
    get_mob_resp = client.get("/api/v1/subscribers/by-mobile/9898444555")
    assert get_mob_resp.status_code == 200
    assert get_mob_resp.json()["id"] == sub_id

    # Not found mobile
    missing_resp = client.get("/api/v1/subscribers/by-mobile/9999999999")
    assert missing_resp.status_code == 404


def test_ported_out_subscriber_business_rule(client: TestClient):
    """Verify ported-out subscribers cannot be reactivated directly."""
    circle_id = get_or_create_circle(client)
    payload = {
        "circle_id": circle_id,
        "mobile_number": "9898555666",
        "full_name": "Porting Test User",
        "sim_card_number": "8991005555666677778",
        "status": "active",
    }
    create_resp = client.post("/api/v1/subscribers/", json=payload)
    sub_id = create_resp.json()["id"]

    # 1. Port out the subscriber
    port_out_resp = client.put(
        f"/api/v1/subscribers/{sub_id}",
        json={"status": "ported_out"},
    )
    assert port_out_resp.status_code == 200
    assert port_out_resp.json()["status"] == "ported_out"
    assert port_out_resp.json()["ported_out_at"] is not None

    # 2. Attempt to reactivate ported-out subscriber directly -> Should fail with 400 Bad Request
    reactivate_resp = client.put(
        f"/api/v1/subscribers/{sub_id}",
        json={"status": "active"},
    )
    assert reactivate_resp.status_code == 400
    assert reactivate_resp.json()["error"]["code"] == "BAD_REQUEST"
    assert "ported-out subscribers cannot be reactivated directly" in reactivate_resp.json()["error"]["message"].lower()


def test_delete_subscriber(client: TestClient):
    """Test deleting a subscriber record."""
    circle_id = get_or_create_circle(client)
    payload = {
        "circle_id": circle_id,
        "mobile_number": "9898666777",
        "full_name": "Temporary Subscriber",
        "sim_card_number": "8991006666777788889",
    }
    create_resp = client.post("/api/v1/subscribers/", json=payload)
    sub_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/subscribers/{sub_id}")
    assert del_resp.status_code == 200

    get_resp = client.get(f"/api/v1/subscribers/{sub_id}")
    assert get_resp.status_code == 404
