from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.schemas.common import HealthCheck


def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    ok = HealthCheck(status="ok")
    with (
        patch("app.api.v1.endpoints.health._check_database", new_callable=AsyncMock, return_value=ok),
        patch("app.api.v1.endpoints.health._check_redis", new_callable=AsyncMock, return_value=ok),
    ):
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "v1"
    assert "timestamp" in data
