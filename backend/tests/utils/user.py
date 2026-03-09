"""
Test utilities for user-related operations.
Uses Repository pattern for database operations.
"""

from httpx import AsyncClient

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from tests.utils.utils import random_email, random_lower_string


async def user_authentication_headers(
    *, client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    """Get authentication headers for a user."""
    data = {"username": email, "password": password}
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/login", data=data)
    # Login sets HttpOnly cookie; use it as Bearer for test requests
    token = response.cookies["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_random_user(session) -> User:
    """Create a random user for testing."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)

    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    return user


async def authentication_token_from_email(
    *, client: AsyncClient, session, email: str
) -> dict[str, str]:
    """Return a valid token for the user with given email."""
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)

    if not user:
        user = await user_repo.create(
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=False,
        )
    else:
        user.hashed_password = hash_password(password)
        await session.flush()

    return await user_authentication_headers(
        client=client, email=email, password=password
    )
