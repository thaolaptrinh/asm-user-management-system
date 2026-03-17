"""
Test PATCH /users/me endpoint - Update current user.
"""

import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.user import UserRepository
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_update_user_me(client, normal_user_token_headers, session):
    """Test update current user."""
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name


@pytest.mark.asyncio
async def test_update_user_me_email_exists(client, normal_user_token_headers, session):
    """Test update user email to existing email returns 409."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    existing_user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"email": existing_user.email}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 409
