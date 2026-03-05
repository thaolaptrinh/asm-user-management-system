"""
All tests use MySQL (MYSQL_DATABASE = app DB + _test). Single DB, single conftest.
Run: make test or ./scripts/run-backend-tests.sh (script resets test DB then runs pytest).
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: unit test (runs on MySQL test DB).")
    config.addinivalue_line("markers", "integration: integration test (MySQL test DB).")


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """MySQL session (test DB); init_db + cleanup User/Item after test."""
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient with get_db overridden to use this MySQL session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
