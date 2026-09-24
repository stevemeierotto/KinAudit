from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_engine, reset_engine
from app.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    cfg.set_main_option("path_separator", "os")
    return cfg


@pytest.fixture(scope="session")
def migrated_database() -> Generator[None, None, None]:
    """Apply migrations once for the test session against real PostgreSQL."""
    reset_engine()
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment guard
        pytest.skip(f"PostgreSQL is not available for genealogy tests: {exc}")

    command.upgrade(_alembic_config(), "head")
    yield
    reset_engine()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    reset_engine()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()


@pytest.fixture
def db_session(migrated_database: None) -> Generator[Session, None, None]:
    """Provide a DB session rolled back after each test."""
    reset_engine()
    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
        reset_engine()


@pytest.fixture
def retrieved_at() -> datetime:
    return datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
