"""
Test logout endpoint.
Uses async pattern with pytest-asyncio.
"""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_logout_returns_200_with_message(client):
    """Test successful logout returns 200 with expected message."""
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful"}


@pytest.mark.asyncio
async def test_logout_clears_access_token_cookie(client):
    """Test that logout clears the access_token cookie."""
    # Set access_token cookie to simulate a logged-in state
    client.cookies.set("access_token", "some_valid_token", domain="test")
    assert client.cookies.get("access_token") == "some_valid_token"

    response = await client.post(f"{settings.API_V1_PREFIX}/auth/logout")
    assert response.status_code == 200

    # Response must instruct the browser to delete access_token (max-age=0)
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie_header
    assert "max-age=0" in set_cookie_header.lower()
