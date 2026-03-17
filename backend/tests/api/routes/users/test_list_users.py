"""
Test GET /users/ endpoint - List users.
"""

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.user import UserRepository
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_retrieve_users(client, superuser_token_headers, session):
    """Test list users as any authenticated user."""
    user_repo = UserRepository(session)
    await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )
    await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
    )
    all_users = response.json()

    assert response.status_code == 200
    assert len(all_users["data"]) >= 2
    assert "count" in all_users
    assert "skip" in all_users
    assert "limit" in all_users
    for item in all_users["data"]:
        assert "email" in item


@pytest.mark.asyncio
async def test_retrieve_users_as_normal_user(
    client, normal_user_token_headers, session
):
    """Test normal user can list users (Phase 1: no RBAC)."""
    user_repo = UserRepository(session)
    await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/",
        headers=normal_user_token_headers,
    )
    all_users = response.json()

    assert response.status_code == 200
    assert "data" in all_users
    assert "count" in all_users


@pytest.mark.asyncio
async def test_list_users_response_shape(client, superuser_token_headers, session):
    """Test each user object contains all expected fields."""
    user_repo = UserRepository(session)
    await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
    )
    all_users = response.json()

    assert response.status_code == 200
    assert "data" in all_users
    assert "count" in all_users
    assert "skip" in all_users
    assert "limit" in all_users

    for item in all_users["data"]:
        assert "id" in item
        assert "email" in item
        assert "full_name" in item
        assert "is_active" in item
        assert "is_superuser" in item
        assert "created_at" in item


@pytest.mark.asyncio
async def test_list_users_empty(client, superuser_token_headers, session):
    """Test list users returns empty paginated response when no users exist (beyond seeded superuser)."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
    )
    all_users = response.json()

    assert response.status_code == 200
    assert "data" in all_users
    assert "count" in all_users
    assert all_users["skip"] == 0
    assert all_users["limit"] == 100


@pytest.mark.asyncio
async def test_list_users_unauthenticated(client):
    """Test unauthenticated request returns 401."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_excludes_hashed_password(
    client, superuser_token_headers, session
):
    """Test hashed_password is never included in the response."""
    user_repo = UserRepository(session)
    await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
    )
    all_users = response.json()

    assert response.status_code == 200
    for item in all_users["data"]:
        assert "password" not in item
        assert "hashed_password" not in item
