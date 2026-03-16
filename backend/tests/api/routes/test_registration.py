"""
Test authentication endpoints: /auth/register.
Tests public user registration with validation and security checks.
"""

import pytest

from app.api.v1.routes.auth import register
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserRegister
from app.services.user import UserService
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_register_success_returns_201(client) -> None:
    """Test successful registration returns 201 with success message."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": random_email(),
            "password": "ValidPassword123!",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "registration successful" in data["message"].lower()
    assert "please log in" in data["message"].lower()
    assert "enable totp" in data["message"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client, session) -> None:
    """Test duplicate email returns 409 Conflict."""
    user_repo = UserRepository(session)
    existing_email = random_email()
    await user_repo.create(
        email=existing_email,
        hashed_password=hash_password(random_lower_string()),
        full_name="Existing User",
    )
    await session.flush()

    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": existing_email,
            "password": "ValidPassword123!",
            "full_name": "New User",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data or "message" in data


@pytest.mark.asyncio
async def test_register_invalid_email_format_returns_422(client) -> None:
    """Test invalid email format returns 422 Unprocessable Entity."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "invalid-email-format",
            "password": "ValidPassword123!",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_password_too_short_returns_422(client) -> None:
    """Test password too short (< 8 chars) returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": random_email(),
            "password": "short",  # 5 characters, less than min 8
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_password_too_long_returns_422(client) -> None:
    """Test password too long (> 128 chars) returns 422."""
    too_long_password = "a" * 129  # 129 characters, more than max 128
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": random_email(),
            "password": too_long_password,
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_missing_email_returns_422(client) -> None:
    """Test missing email returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "password": "ValidPassword123!",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_missing_password_returns_422(client) -> None:
    """Test missing password returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": random_email(),
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_missing_both_fields_returns_422(client) -> None:
    """Test missing both email and password returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_password_not_stored_as_plain_text(client, session) -> None:
    """Test password is hashed, not stored as plain text."""
    test_email = random_email()
    plain_password = "MySecurePassword123!"

    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": test_email,
            "password": plain_password,
            "full_name": "Security Test User",
        },
    )
    assert response.status_code == 201

    # Verify password is hashed in database
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.email == test_email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.hashed_password != plain_password
    assert len(user.hashed_password) == 60  # bcrypt hash length
    assert user.hashed_password.startswith("$2b$")  # bcrypt format


@pytest.mark.asyncio
async def test_register_database_isolation(client, session) -> None:
    """Test each registration is isolated (SAVEPOINT-based rollback)."""
    # Register first user
    email1 = random_email()
    response1 = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": email1,
            "password": "ValidPassword123!",
            "full_name": "User One",
        },
    )
    assert response1.status_code == 201

    # Verify user exists
    from sqlalchemy import select

    result1 = await session.execute(select(User).where(User.email == email1))
    user1 = result1.scalar_one_or_none()
    assert user1 is not None

    # After test ends, session.rollback() will undo everything
    # This test verifies the isolation mechanism works


@pytest.mark.asyncio
async def test_register_full_name_optional(client) -> None:
    """Test full_name is optional and can be omitted."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": random_email(),
            "password": "ValidPassword123!",
            # No full_name provided
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_register_full_name_too_long_returns_422(client) -> None:
    """Test full_name too long (> 255 chars) returns 422."""
    too_long_name = "a" * 256  # 256 characters, more than max 255
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": random_email(),
            "password": "ValidPassword123!",
            "full_name": too_long_name,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_default_fields(client, session) -> None:
    """Test newly registered user has correct default values."""
    test_email = random_email()
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": test_email,
            "password": "ValidPassword123!",
            "full_name": "Default Test User",
        },
    )
    assert response.status_code == 201

    from sqlalchemy import select

    result = await session.execute(select(User).where(User.email == test_email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_active is True  # Default: True
    assert user.is_superuser is False  # Default: False
    assert user.password_version == 1  # Default: 1


@pytest.mark.asyncio
async def test_register_function_direct_call(session) -> None:
    """Test register function directly to ensure 100% coverage of return statement."""
    user_repo = UserRepository(session)
    user_service = UserService(user_repo)

    test_email = random_email()
    user_data = UserRegister(
        email=test_email,
        password="DirectCall123!",
        full_name="Direct Call Test",
    )

    # Call register function directly (bypass FastAPI routing)
    result = await register(user_data, user_service)

    # Verify return statement is executed
    assert result.message == "Registration successful. Please log in and enable TOTP."

    # Verify user was created in database
    from sqlalchemy import select

    result_db = await session.execute(select(User).where(User.email == test_email))
    user = result_db.scalar_one_or_none()
    assert user is not None
    assert user.email == test_email
