"""
Test GET /users/me endpoint - Get current user.
"""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_get_users_superuser_me(client, superuser_token_headers):
    """Test get current user as superuser."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=superuser_token_headers,
    )
    current_user = response.json()
    assert response.status_code == 200
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is True
    assert current_user["email"] == settings.FIRST_SUPERUSER


@pytest.mark.asyncio
async def test_get_users_normal_user_me(client, normal_user_token_headers):
    """Test get current user as normal user."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=normal_user_token_headers,
    )
    current_user = response.json()
    assert response.status_code == 200
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False


@pytest.mark.asyncio
async def test_get_own_user_with_custom_token(client, session):
    """Test get own user with custom token."""
    from app.core.security import create_access_token
    from app.repositories.user import UserRepository
    from app.core.security import hash_password
    from tests.utils.utils import random_email, random_lower_string

    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    await session.flush()

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=headers,
    )
    assert response.status_code == 200
    api_user = response.json()
    assert api_user["email"] == username
