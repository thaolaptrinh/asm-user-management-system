"""
Tests for user repository and auth service operations.
Rewritten for new async architecture (SQLAlchemy 2.0 + AsyncSession).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.auth import AuthService
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    assert user.email == email
    assert hasattr(user, "hashed_password")


@pytest.mark.asyncio
async def test_authenticate_user(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    auth_service = AuthService(user_repo)
    authenticated_user = await auth_service.authenticate(email=email, password=password)
    assert authenticated_user
    assert authenticated_user.email == email


@pytest.mark.asyncio
async def test_not_authenticate_user(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    auth_service = AuthService(user_repo)
    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate(email=email, password=password)


@pytest.mark.asyncio
async def test_check_if_user_is_active(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    assert user.is_active is True


@pytest.mark.asyncio
async def test_check_if_user_is_active_inactive(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=False,
        is_superuser=False,
    )
    assert user.is_active is False


@pytest.mark.asyncio
async def test_check_if_user_is_superuser(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
    )
    assert user.is_superuser is True


@pytest.mark.asyncio
async def test_check_if_user_is_superuser_normal_user(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    assert user.is_superuser is False


@pytest.mark.asyncio
async def test_get_user(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
    )
    user_2 = await user_repo.get_by_id(user.id)
    assert user_2
    assert user.email == user_2.email


@pytest.mark.asyncio
async def test_update_user(session: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
    )
    new_password = random_lower_string()
    await user_repo.update(user, hashed_password=hash_password(new_password))

    user_2 = await user_repo.get_by_id(user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
