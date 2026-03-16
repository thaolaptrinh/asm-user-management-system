"""
Test authentication endpoints.
Uses async pattern with pytest-asyncio.
"""

import pytest

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.utils import create_user_password_reset_token, generate_password_reset_token
from tests.utils.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_get_access_token(client):
    """Test login returns temp_token in JSON body (step 1 of 2FA)."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "temp_token" in data
    assert data["temp_token"]
    assert "message" in data
    # Login no longer sets a cookie — access_token comes after TOTP verify
    assert "access_token" not in response.cookies


@pytest.mark.asyncio
async def test_get_access_token_incorrect_password(client):
    """Test login with incorrect password."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_access_token_inactive_user_returns_401(client, session):
    """Login with is_active=False user -> 401."""
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=False,
        is_superuser=False,
    )
    await session.flush()

    login_data = {
        "username": user.email,
        "password": random_lower_string(),
    }
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    assert response.status_code == 401
    # Generic message to prevent user enumeration
    assert "invalid email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_recovery_password(client, normal_user_token_headers):
    """Test password recovery endpoint."""
    email = "test@example.com"
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


@pytest.mark.asyncio
async def test_recovery_password_user_not_exists(client, normal_user_token_headers):
    """Test password recovery with non-existent user - should not reveal user existence."""
    email = "nonexistent@example.com"
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


@pytest.mark.asyncio
async def test_reset_password(client, session):
    """Test password reset with valid token."""
    email = random_email()
    password = random_lower_string()
    new_password = random_lower_string()

    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    await session.flush()

    token = await create_user_password_reset_token(session, email=email)
    assert token is not None

    data = {"new_password": new_password, "token": token}

    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/reset-password/",
        json=data,
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password updated successfully"}

    await session.refresh(user)
    verified = verify_password(new_password, user.hashed_password)
    assert verified


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client, superuser_token_headers):
    """Test password reset with invalid token."""
    data = {"new_password": "changethis", "token": "invalid"}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reset_password_valid_token_user_deleted(client, session):
    """Test password reset with valid token but user deleted."""
    email = random_email()
    password = random_lower_string()

    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    await session.flush()

    token = await create_user_password_reset_token(session, email=email)
    assert token is not None

    await session.delete(user)
    await session.flush()

    data = {"new_password": "newpass123", "token": token}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/reset-password/",
        json=data,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_returns_temp_token_when_totp_enabled(client, session):
    """Login returns temp_token even when user has TOTP enabled (no access_token cookie)."""
    from app.models.totp_secret import TotpSecret

    email = random_email()
    password = random_lower_string()

    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )
    await session.flush()

    totp = TotpSecret(
        user_id=str(user.id),
        secret="JBSWY3DPEHPK3PXP",
        algorithm="SHA1",
        digits=6,
        period=30,
        is_verified=True,
        last_used_at=None,
    )
    session.add(totp)
    await session.flush()

    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "temp_token" in data
    assert data["temp_token"]
    # access_token cookie must NOT be set at login stage — only after TOTP verify
    assert "access_token" not in response.cookies


@pytest.mark.asyncio
async def test_login_with_bcrypt_password(client, session):
    """Test that logging in with a bcrypt password hash returns temp_token."""
    email = random_email()
    password = random_lower_string()

    import bcrypt

    bcrypt_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user_repo = UserRepository(session)
    await user_repo.create(
        email=email,
        hashed_password=bcrypt_hash,
        is_active=True,
        is_superuser=False,
    )

    login_data = {"username": email, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    assert response.status_code == 200
    assert "temp_token" in response.json()


@pytest.mark.asyncio
async def test_login_with_bcrypt_password_keeps_hash(client, session):
    """Test that logging in with bcrypt password keeps the hash (no upgrade)."""
    email = random_email()
    password = random_lower_string()

    import bcrypt

    bcrypt_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=email,
        hashed_password=bcrypt_hash,
        is_active=True,
        is_superuser=False,
    )

    original_hash = user.hashed_password

    login_data = {"username": email, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    assert response.status_code == 200
    assert "temp_token" in response.json()

    await session.refresh(user)
    assert user.hashed_password == original_hash
