import pytest
from fastapi.testclient import TestClient

from app.database.session import reset_engine
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    reset_engine()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
