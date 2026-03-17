"""
Test DELETE /users/{id} endpoint - Delete user by ID.
"""

import uuid

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.user import UserRepository
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_delete_user(client, superuser_token_headers, session):
    """Test delete user as superuser."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    response = await client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"

    deleted_user = await user_repo.get_by_id(user.id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_delete_user_not_exists(client, superuser_token_headers):
    """Test delete non-existing user returns 404."""
    response = await client.delete(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_user_invalid_path(client, superuser_token_headers):
    """Test DELETE /users/me returns 422 (path validation error: 'me' is not a UUID)."""
    response = await client.delete(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_unauthenticated(client):
    """Test unauthenticated request returns 401."""
    response = await client.delete(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
    )
    assert response.status_code == 401
