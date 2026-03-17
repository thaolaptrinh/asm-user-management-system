"""
Test PUT /users/me/password endpoint - Change password.
"""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_change_password_success(client, normal_user_token_headers):
    """Test successful password change via API."""
    response = await client.put(
        f"{settings.API_V1_PREFIX}/users/me/password",
        headers=normal_user_token_headers,
        json={"current_password": "testpassword123", "new_password": "NewPassword456!"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_change_password_unauthorized(client):
    """Test change password without auth token returns 401."""
    response = await client.put(
        f"{settings.API_V1_PREFIX}/users/me/password",
        json={"current_password": "testpassword123", "new_password": "NewPassword456!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_validation_errors(client, normal_user_token_headers):
    """Test password validation."""
    # Test password reuse
    response = await client.put(
        f"{settings.API_V1_PREFIX}/users/me/password",
        headers=normal_user_token_headers,
        json={"current_password": "testpassword123", "new_password": "testpassword123"},
    )
    assert response.status_code == 422

    # Test weak password
    response = await client.put(
        f"{settings.API_V1_PREFIX}/users/me/password",
        headers=normal_user_token_headers,
        json={"current_password": "TestPassword123!", "new_password": "password"},
    )
    assert response.status_code == 422
