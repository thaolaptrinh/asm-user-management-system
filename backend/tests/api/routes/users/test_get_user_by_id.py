"""
Test GET /users/{id} endpoint - Get user by ID.
"""

import uuid

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.user import UserRepository
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_get_existing_user_as_superuser(client, superuser_token_headers, session):
    """Test get existing user as superuser."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    api_user = response.json()

    existing_user = await user_repo.get_by_email(username)
    assert existing_user is not None
    assert existing_user.email == api_user["email"]


@pytest.mark.asyncio
async def test_get_non_existing_user_as_superuser(client, superuser_token_headers):
    """Test get non-existing user returns 404."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_existing_user_as_normal_user(
    client, normal_user_token_headers, session
):
    """Test normal user can get other user details (Phase 1: no RBAC)."""
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_non_existing_user_as_normal_user(client, normal_user_token_headers):
    """Test normal user gets 404 for non-existing user (Phase 1: no RBAC)."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
