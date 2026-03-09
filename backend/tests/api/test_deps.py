"""Tests for app.api.v1.deps (get_current_user, get_current_superuser)."""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_returns_401(client: AsyncClient) -> None:
    """Invalid or malformed token -> 401 Could not validate credentials."""
    r = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_valid_token_user_not_found_returns_401(
    client: AsyncClient,
) -> None:
    """Valid JWT but user_id not in DB -> 401 User not found."""
    unknown_id = uuid.uuid4()
    token = create_access_token(
        subject=str(unknown_id), expires_delta=timedelta(minutes=15)
    )
    r = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_get_current_user_inactive_returns_401(
    client: AsyncClient, session: AsyncSession
) -> None:
    """Valid token but user is_active=False -> 401 Account is inactive."""
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=False,
        is_superuser=False,
    )
    token = create_access_token(
        subject=str(user.id), expires_delta=timedelta(minutes=15)
    )
    r = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401
    assert "inactive" in r.json()["detail"].lower()
