"""
Test password_version in access token creation and validation.
Tests for the bug fix where token creation was missing password_version parameter.
"""

import pytest
from datetime import timedelta
from app.core.security import (
    create_access_token,
    decode_access_token,
    create_temp_token,
)


@pytest.mark.unit
def test_create_access_token_includes_password_version():
    """Test that create_access_token includes password_version in token payload."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    password_version = 5

    token = create_access_token(user_id, password_version)

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["password_version"] == password_version
    assert payload["type"] == "access"


@pytest.mark.unit
def test_create_access_token_default_password_version():
    """Test that create_access_token defaults to password_version=1 if not provided."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    token = create_access_token(user_id)

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["password_version"] == 1
    assert payload["type"] == "access"


@pytest.mark.unit
def test_create_temp_token_does_not_include_password_version():
    """Test that create_temp_token does NOT include password_version (uses temp type)."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    token = create_temp_token(user_id)

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert "password_version" not in payload
    assert payload["type"] == "temp"


@pytest.mark.unit
def test_create_access_token_with_expires_delta():
    """Test that create_access_token respects custom expires_delta."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    password_version = 2
    custom_expiry = timedelta(hours=2)

    token = create_access_token(user_id, password_version, custom_expiry)

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["password_version"] == password_version
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload
