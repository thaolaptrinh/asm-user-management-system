"""
Test PATCH /users/{id} endpoint - Update user by ID.
"""

import uuid

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.user import UserRepository
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_update_user(client, superuser_token_headers, session):
    """Test update user as superuser."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"full_name": "Updated_full_name"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    updated_user = response.json()

    # Validate ALL response fields
    assert "id" in updated_user
    assert "email" in updated_user
    assert "full_name" in updated_user
    assert "is_active" in updated_user
    assert "is_superuser" in updated_user
    assert "created_at" in updated_user
    assert "updated_at" in updated_user

    # Validate updated field value
    assert updated_user["full_name"] == "Updated_full_name"


@pytest.mark.asyncio
async def test_update_user_not_exists(client, superuser_token_headers):
    """Test update non-existing user returns 404."""
    data = {"full_name": "Updated_full_name"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    # Validate exact error message
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_user_email_exists(client, superuser_token_headers, session):
    """Test update user email to existing email returns 409."""
    user_repo = UserRepository(session)
    existing_user = await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    username = random_email()
    password = random_lower_string()
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"email": existing_user.email}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
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
async def test_update_user_unauthenticated_returns_401(client):
    """Test update user without authentication returns 401."""
    data = {"full_name": "Updated Name"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        json=data,
        # Note: No headers parameter - no authentication token
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_invalid_email_format_returns_422(
    client, superuser_token_headers, session
):
    """Test update user with invalid email format returns 422."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"email": "invalid-email-format"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_invalid_uuid_returns_422(client):
    """Test update user with invalid UUID returns 422."""
    data = {"full_name": "Updated Name"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/invalid-uuid",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_full_name_too_long_returns_422(
    client, superuser_token_headers, session
):
    """Test update user with full_name too long (> 255 chars) returns 422."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"full_name": "a" * 256}  # > 255 chars
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_multiple_fields(client, superuser_token_headers, session):
    """Test update user with multiple fields at once."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"full_name": "Updated Name", "is_active": False}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["full_name"] == "Updated Name"
    assert updated_user["is_active"] is False
