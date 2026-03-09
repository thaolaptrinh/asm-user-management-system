"""
Test configuration using async pattern with pytest-asyncio.
Uses ASGITransport (in-process, no real HTTP socket) for fast endpoint testing.
"""

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_session
from app.main import app
from app.models.user import User


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "asyncio: mark test as async.")
    config.addinivalue_line("markers", "unit: unit test.")
    config.addinivalue_line("markers", "integration: integration test.")

    app.state.limiter.enabled = False
    from app.api.v1.routes.auth import limiter as auth_limiter
    auth_limiter.enabled = False


@pytest_asyncio.fixture
async def engine():
    """Create a new engine for each test to avoid event loop issues."""
    test_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Async session with SAVEPOINT-based isolation per test.

    join_transaction_mode="create_savepoint" ensures that any session.commit()
    or session.flush() inside a test creates a SAVEPOINT instead of a real DB
    commit — so the outer conn.rollback() at teardown always undoes everything,
    leaving the DB clean for the next test without truncating tables.
    """
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield session

        await session.close()
        await conn.rollback()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient backed by the test session — no real HTTP, no DB side-effects."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    """Authentication headers for the seeded superuser account."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    # Login sets HttpOnly cookie; extract it for use as Bearer in tests
    # (deps.py accepts both cookie and Bearer token)
    token = response.cookies["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def normal_user_token_headers(
    client: AsyncClient, session: AsyncSession
) -> dict[str, str]:
    """Authentication headers for a fresh normal user created per-test."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"

    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()  # write to DB within the test transaction, no real commit

    login_data = {"username": email, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    token = response.cookies["access_token"]
    return {"Authorization": f"Bearer {token}"}
