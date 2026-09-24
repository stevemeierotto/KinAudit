from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_liveness(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_with_db(client: TestClient) -> None:
    with patch(
        "app.api.routes.health.check_database_connection",
        return_value=True,
    ):
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "reachable"}


def test_health_ready_fails_without_db(client: TestClient) -> None:
    with patch(
        "app.api.routes.health.check_database_connection",
        return_value=False,
    ):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unreachable"}
