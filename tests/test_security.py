
import os
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

# Configure test authentication before importing the app
os.environ["FLOWFORGE_API_KEY"] = "flowforge-test-key-only"

from app.main import app

client = TestClient(app)

HEADERS = {"X-API-Key": "flowforge-test-key-only"}

VALID_REQUEST = {
    "customer_name": "Security Test",
    "email": "security@example.com",
    "message": "I need help with billing.",
    "priority": "medium",
}


def test_missing_api_key():
    response = client.post("/requests", json=VALID_REQUEST)
    assert response.status_code == 401


def test_invalid_api_key():
    response = client.post(
        "/requests",
        json=VALID_REQUEST,
        headers={"X-API-Key": "incorrect-key"},
    )
    assert response.status_code == 401


def test_valid_api_key():
    mock_response = httpx.Response(
        200,
        request=httpx.Request("POST", "http://localhost/webhook"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = client.post(
            "/requests",
            json=VALID_REQUEST,
            headers=HEADERS,
        )

    assert response.status_code == 200
    assert response.json()["status"] == "forwarded_to_n8n"


def test_n8n_connection_failure():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        response = client.post(
            "/requests",
            json=VALID_REQUEST,
            headers=HEADERS,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Automation service is temporarily unavailable"
    )


def test_n8n_timeout():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ReadTimeout("Request timed out")

        response = client.post(
            "/requests",
            json=VALID_REQUEST,
            headers=HEADERS,
        )

    assert response.status_code == 504
    assert response.json()["detail"] == "Automation service timed out"


def test_message_too_long():
    invalid_request = {
        **VALID_REQUEST,
        "message": "A" * 5001,
    }

    response = client.post(
        "/requests",
        json=invalid_request,
        headers=HEADERS,
    )

    assert response.status_code == 422
