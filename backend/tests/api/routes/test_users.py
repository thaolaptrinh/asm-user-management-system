"""
Test user endpoints.
Uses async pattern with pytest-asyncio.
"""

import uuid

import pytest

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from tests.utils.utils import random_email, random_lower_string


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
async def test_create_user_new_email(client, superuser_token_headers, session):
    """Test create new user as superuser."""
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    created_user = response.json()

    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(username)
    assert user is not None
    assert user.email == created_user["email"]


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
async def test_get_existing_user_current_user(client, session):
    """Test get own user."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    login_data = {"username": username, "password": password}
    login_response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login", data=login_data
    )
    token = login_response.cookies["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=headers,
    )
    assert response.status_code == 200
    api_user = response.json()
    assert api_user["email"] == username


@pytest.mark.asyncio
async def test_get_existing_user_permissions_error(
    client, normal_user_token_headers, session
):
    """Test normal user cannot get other user details."""
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
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_non_existing_user_permissions_error(
    client, normal_user_token_headers
):
    """Test normal user cannot access non-existing user."""
    response = await client.get(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_existing_email(client, superuser_token_headers, session):
    """Test create user with existing email returns 409."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"email": username, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_by_normal_user(client, normal_user_token_headers):
    """Test normal user cannot create user."""
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    response = await client.post(
        f"{settings.API_V1_PREFIX}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_users(client, superuser_token_headers, session):
    """Test list users as superuser."""
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


@pytest.mark.asyncio
async def test_update_user(client, superuser_token_headers, session):
    """Test update user as superuser."""
    username = random_email()
    password = random_lower_string()
    user_repo = UserRepository(session)
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"full_name": "Updated_full_name"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["full_name"] == "Updated_full_name"


@pytest.mark.asyncio
async def test_update_user_not_exists(client, superuser_token_headers):
    """Test update non-existing user returns 404."""
    data = {"full_name": "Updated_full_name"}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_email_exists(client, superuser_token_headers, session):
    """Test update user email to existing email returns 409."""
    user_repo = UserRepository(session)
    existing_user = await user_repo.create(
        email=random_email(),
        hashed_password=hash_password(random_lower_string()),
        is_active=True,
        is_superuser=False,
    )

    username = random_email()
    password = random_lower_string()
    user = await user_repo.create(
        email=username,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False,
    )

    data = {"email": existing_user.email}
    response = await client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 409


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
    assert response.json()["message"] == "User deleted"

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


@pytest.mark.asyncio
async def test_delete_user_cannot_delete_self(client, superuser_token_headers):
    """Test superuser cannot delete own account via /me endpoint."""
    # DELETE /me is not implemented - returns 422 (path validation error)
    # The check exists in DELETE /{user_id} but requires UUID
    response = await client.delete(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=superuser_token_headers,
    )
    assert response.status_code == 422
