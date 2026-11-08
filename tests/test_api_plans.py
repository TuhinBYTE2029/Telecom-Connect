"""Integration tests for Prepaid Plans API endpoints."""
from fastapi.testclient import TestClient


def test_create_plan_and_computed_fields(client: TestClient):
    """Test creating a plan and verifying data_allowance_gb computation."""
    payload = {
        "code": "TC-API-249",
        "name": "Ahmedabad Super 249",
        "price": 249.00,
        "validity_days": 28,
        "data_allowance_mb": 1536,  # 1.5 GB
        "is_unlimited_data": False,
        "talktime_minutes": -1,
        "is_unlimited_calls": True,
        "sms_count": 100,
        "plan_type": "DAILY_DATA",
        "description": "Daily 1.5GB plan for Ahmedabad users",
        "is_active": True,
    }
    response = client.post("/api/v1/plans/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "TC-API-249"
    assert data["price"] == "249.00"
    assert data["data_allowance_mb"] == 1536
    assert data["data_allowance_gb"] == 1.5


def test_create_plan_duplicate_code(client: TestClient):
    """Test duplicate plan code raises 409 Conflict."""
    payload = {
        "code": "TC-API-DUP",
        "name": "Duplicate Plan",
        "price": 199.00,
        "validity_days": 28,
        "data_allowance_mb": 1024,
    }
    resp1 = client.post("/api/v1/plans/", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/plans/", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"


def test_create_plan_invalid_values(client: TestClient):
    """Test validation errors for invalid price and validity."""
    # Price <= 0 rejected by Pydantic schema
    invalid_price = {
        "code": "TC-INV-1",
        "name": "Invalid Price",
        "price": -10.00,
        "validity_days": 28,
    }
    resp1 = client.post("/api/v1/plans/", json=invalid_price)
    assert resp1.status_code == 422

    # Validity <= 0 rejected by Pydantic schema
    invalid_validity = {
        "code": "TC-INV-2",
        "name": "Invalid Validity",
        "price": 100.00,
        "validity_days": 0,
    }
    resp2 = client.post("/api/v1/plans/", json=invalid_validity)
    assert resp2.status_code == 422


def test_list_plans_and_filtering(client: TestClient):
    """Test listing plans with price range, validity, and data allowance filters."""
    # Create sample plans for test
    client.post(
        "/api/v1/plans/",
        json={
            "code": "TC-SRCH-250",
            "name": "Super Ahmedabad 250",
            "price": 250.00,
            "validity_days": 28,
            "data_allowance_mb": 1536,
        },
    )
    client.post(
        "/api/v1/plans/",
        json={
            "code": "TC-SRCH-550",
            "name": "Heavy User 550",
            "price": 550.00,
            "validity_days": 56,
            "data_allowance_mb": 3072,
        },
    )

    # List all
    response = client.get("/api/v1/plans/?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

    # Filter by price range
    filtered_resp = client.get("/api/v1/plans/?min_price=200&max_price=300")
    assert filtered_resp.status_code == 200
    filtered_data = filtered_resp.json()
    assert len(filtered_data["items"]) >= 1
    for item in filtered_data["items"]:
        price = float(item["price"])
        assert 200 <= price <= 300

    # Search by code or keyword
    search_resp = client.get("/api/v1/plans/?search=Super")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert any("super" in item["name"].lower() for item in search_data["items"])


def test_get_and_update_plan(client: TestClient):
    """Test retrieving and updating plan."""
    payload = {
        "code": "TC-UPD-399",
        "name": "Update Plan 399",
        "price": 399.00,
        "validity_days": 56,
        "data_allowance_mb": 2048,
    }
    create_resp = client.post("/api/v1/plans/", json=payload)
    plan_id = create_resp.json()["id"]

    # Get by ID
    get_resp = client.get(f"/api/v1/plans/{plan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["code"] == "TC-UPD-399"

    # Update price and description
    update_payload = {
        "price": 419.00,
        "description": "Revised tariff for 56 days pack",
    }
    update_resp = client.put(f"/api/v1/plans/{plan_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["price"] == "419.00"
    assert update_resp.json()["description"] == "Revised tariff for 56 days pack"


def test_delete_plan(client: TestClient):
    """Test deleting an unreferenced plan."""
    payload = {
        "code": "TC-DEL-99",
        "name": "Delete Plan 99",
        "price": 99.00,
        "validity_days": 14,
        "data_allowance_mb": 512,
    }
    create_resp = client.post("/api/v1/plans/", json=payload)
    plan_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/plans/{plan_id}")
    assert del_resp.status_code == 200

    get_resp = client.get(f"/api/v1/plans/{plan_id}")
    assert get_resp.status_code == 404
