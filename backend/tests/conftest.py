"""
Test configuration using async pattern with pytest-asyncio.
Uses ASGITransport (in-process, no real HTTP socket) for fast endpoint testing.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.security import create_access_token, create_temp_token, hash_password
from app.db.session import get_session
from app.main import app
from app.models.totp_secret import TotpSecret
from app.models.user import User
from app.repositories.totp_secret import TotpSecretRepository
from app.repositories.user import UserRepository
from app.repositories.audit_log import AuditLogRepository
from app.services.totp import TotpService
from app.services.user import UserService


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "asyncio: mark test as async.")
    config.addinivalue_line("markers", "unit: unit test.")
    config.addinivalue_line("markers", "integration: integration test.")

    app.state.limiter.enabled = False
    from app.api.v1.routes.auth import limiter as auth_limiter
    from app.api.v1.routes.totp import limiter as totp_limiter

    auth_limiter.enabled = False
    totp_limiter.enabled = False


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
async def superuser_token_headers(session: AsyncSession) -> dict[str, str]:
    """Authentication headers for the seeded superuser account (token created directly)."""
    from sqlalchemy import select

    result = await session.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    )
    user = result.scalar_one_or_none()
    if user is None:
        pytest.skip("Superuser not seeded in test DB")
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def normal_user_token_headers(session: AsyncSession) -> dict[str, str]:
    """Authentication headers for a fresh normal user (token created directly)."""
    user = User(
        id=uuid.uuid4(),
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


# TOTP Fixtures


@pytest_asyncio.fixture
async def totp_repo(session: AsyncSession) -> TotpSecretRepository:
    """Create TOTP repository fixture."""
    return TotpSecretRepository(session)


@pytest.fixture
def totp_service(totp_repo: TotpSecretRepository) -> TotpService:
    """Create TOTP service fixture."""
    return TotpService(totp_repo)


@pytest_asyncio.fixture
async def sample_user_with_totp(session: AsyncSession) -> User:
    """Create a sample user with TOTP enabled."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"totp_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    totp = TotpSecret(
        user_id=str(user_id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    return user


@pytest.fixture
def valid_totp_code() -> str:
    """Mock valid TOTP code for testing."""
    return "123456"


@pytest.fixture
def mock_qr_code() -> str:
    """Mock QR code base64 string for testing."""
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest_asyncio.fixture
async def totp_user_access_headers(session: AsyncSession) -> dict[str, str]:
    """Access token headers for a user who has completed full TOTP login."""
    user = User(
        id=uuid.uuid4(),
        email=f"totp_access_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def totp_user_temp_headers(session: AsyncSession) -> dict[str, str]:
    """Temp token headers simulating post-login state (before TOTP verify)."""
    user = User(
        id=uuid.uuid4(),
        email=f"totp_temp_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    token = create_temp_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def audit_repo(session: AsyncSession) -> AuditLogRepository:
    """Create AuditLog repository fixture."""
    return AuditLogRepository(session)


@pytest.fixture
def user_service(session: AsyncSession) -> UserService:
    """Create UserService fixture."""
    return UserService(UserRepository(session))


@pytest_asyncio.fixture
async def normal_user(session: AsyncSession) -> User:
    """Create a normal user with TOTP enabled for testing password changes."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"normal_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("TestPassword123!"),
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    totp = TotpSecret(
        user_id=str(user_id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    return user
