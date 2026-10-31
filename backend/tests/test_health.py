"""
Health endpoint tests — run without a database (uses TestClient in-process).
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=True)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure():
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "app" in body
    assert "environment" in body
    assert "version" in body


def test_health_content_type_is_json():
    response = client.get("/health")
    assert "application/json" in response.headers.get("content-type", "")


def test_docs_endpoint_available():
    """Swagger UI should be accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
