"""Integration tests for Telecom Circles API endpoints."""
from fastapi.testclient import TestClient


def test_create_circle(client: TestClient):
    """Test creating a new telecom circle."""
    payload = {
        "code": "RJ",
        "name": "Rajasthan Telecom Circle",
        "state": "Rajasthan",
        "is_active": True,
    }
    response = client.post("/api/v1/circles/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "RJ"
    assert data["name"] == "Rajasthan Telecom Circle"
    assert data["id"] is not None


def test_create_circle_duplicate_code(client: TestClient):
    """Test duplicate circle code raises 409 Conflict."""
    payload = {
        "code": "PB",
        "name": "Punjab Telecom Circle",
        "state": "Punjab",
        "is_active": True,
    }
    resp1 = client.post("/api/v1/circles/", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/circles/", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"


def test_list_and_search_circles(client: TestClient):
    """Test listing, searching and pagination of circles."""
    # Ensure a circle exists to search
    client.post(
        "/api/v1/circles/",
        json={
            "code": "SRC",
            "name": "Search Test Circle",
            "state": "Gujarat",
            "is_active": True,
        },
    )

    # List circles
    response = client.get("/api/v1/circles/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1

    # Search circle by code
    search_resp = client.get("/api/v1/circles/?search=SRC")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert any(c["code"] == "SRC" for c in search_data["items"])


def test_get_circle_by_id(client: TestClient):
    """Test retrieving circle by ID."""
    payload = {
        "code": "HP",
        "name": "Himachal Pradesh Circle",
        "state": "Himachal Pradesh",
        "is_active": True,
    }
    create_resp = client.post("/api/v1/circles/", json=payload)
    circle_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/circles/{circle_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["code"] == "HP"

    # Not found check
    missing_resp = client.get("/api/v1/circles/999999")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error"]["code"] == "NOT_FOUND"


def test_update_circle(client: TestClient):
    """Test updating circle details."""
    payload = {
        "code": "UP",
        "name": "Uttar Pradesh West",
        "state": "Uttar Pradesh",
        "is_active": True,
    }
    create_resp = client.post("/api/v1/circles/", json=payload)
    circle_id = create_resp.json()["id"]

    update_payload = {"name": "UP West & Uttarakhand", "is_active": False}
    update_resp = client.put(f"/api/v1/circles/{circle_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["name"] == "UP West & Uttarakhand"
    assert updated_data["is_active"] is False


def test_delete_circle(client: TestClient):
    """Test deleting an unreferenced circle."""
    payload = {
        "code": "GA",
        "name": "Goa Circle",
        "state": "Goa",
        "is_active": True,
    }
    create_resp = client.post("/api/v1/circles/", json=payload)
    circle_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/circles/{circle_id}")
    assert del_resp.status_code == 200

    # Ensure deleted
    get_resp = client.get(f"/api/v1/circles/{circle_id}")
    assert get_resp.status_code == 404
