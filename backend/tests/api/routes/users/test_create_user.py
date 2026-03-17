"""
Test POST /users/ endpoint - Create user.
"""

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.user import UserRepository
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_create_user_new_email(client, superuser_token_headers, session):
    """Test create new user as superuser."""
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    created_user = response.json()

    # Validate all response fields
    assert "id" in created_user
    assert "email" in created_user
    assert "full_name" in created_user
    assert "is_active" in created_user
    assert "created_at" in created_user
    assert created_user["email"] == username
    assert created_user["is_active"] is True

    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(username)
    assert user is not None
    assert user.email == created_user["email"]


@pytest.mark.asyncio
async def test_create_user_existing_email(client, superuser_token_headers, session):
    """Test create user with existing email returns 409."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"email": username, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409
    # Validate exact error message
    assert (
        response.json()["detail"]
        == "The user with this email already exists in the system"
    )


@pytest.mark.asyncio
async def test_create_user_by_normal_user(client, normal_user_token_headers):
    """Test normal user can create user (Phase 1: no RBAC)."""
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_user_unauthenticated_returns_401(client):
    """Test create user without authentication returns 401."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        json={
            "email": random_email(),
            "password": random_lower_string(),
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_user_invalid_email_format_returns_422(
    client, superuser_token_headers
):
    """Test create user with invalid email format returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "email": "invalid-email-format",
            "password": random_lower_string(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_password_too_short_returns_422(
    client, superuser_token_headers
):
    """Test create user with password too short (< 8 chars) returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": "short",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_password_too_long_returns_422(
    client, superuser_token_headers
):
    """Test create user with password too long (> 128 chars) returns 422."""
    too_long_password = "a" * 129
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": too_long_password,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_email_returns_422(client, superuser_token_headers):
    """Test create user without email returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "password": random_lower_string(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_password_returns_422(
    client, superuser_token_headers
):
    """Test create user without password returns 422."""
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_boundary_password_lengths(client, superuser_token_headers):
    """Test create user with boundary password lengths (8 and 64 chars)."""
    # Test exactly 8 characters (should pass)
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": "12345678",
        },
    )
    assert response.status_code == 201

    # Test exactly 64 characters (should pass)
    valid_password = "a" * 64
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": valid_password,
        },
    )
    assert response.status_code == 201
