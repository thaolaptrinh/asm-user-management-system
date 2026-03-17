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
