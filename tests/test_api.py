
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["project"] == "FlowForge AI"


def test_invalid_request():
    response = client.post(
        "/requests",
        json={
            "customer_name": "",
            "email": "invalid-email",
            "message": "",
            "priority": "high",
        },
        headers={"X-API-Key": "flowforge-test-key-only"},
    )
    assert response.status_code == 422


def test_invalid_priority():
    response = client.post(
        "/requests",
        json={
            "customer_name": "Test Customer",
            "email": "test@example.com",
            "message": "Test request",
            "priority": "urgent",
        },
        headers={"X-API-Key": "flowforge-test-key-only"},
    )
    assert response.status_code == 422

