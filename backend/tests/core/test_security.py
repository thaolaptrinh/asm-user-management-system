from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_temp_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ============== PASSWORD HASHING TESTS ==============


def test_hash_password_returns_string() -> None:
    """Test that hash_password returns a string."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert len(hashed) == 60


def test_verify_password_correct_returns_true() -> None:
    """Test that verifying correct password returns True."""
    password = "CorrectPassword456!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect_returns_false() -> None:
    """Test that verifying incorrect password returns False."""
    password = "OriginalPassword123!"
    hashed = hash_password(password)
    wrong_password = "WrongPassword789!"
    assert verify_password(wrong_password, hashed) is False


def test_verify_password_empty_string_returns_false() -> None:
    """Test that verifying empty string password returns False."""
    password = "ValidPassword456!"
    hashed = hash_password(password)
    assert verify_password("", hashed) is False


def test_hash_same_password_twice_different_hashes() -> None:
    """Test that hashing same password twice produces different hashes (random salt)."""
    password = "SamePassword789!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_hash_password_format() -> None:
    """Test that hashed password has correct bcrypt format."""
    password = "FormatTest123!"
    hashed = hash_password(password)
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60


# ============== ACCESS TOKEN TESTS ==============


def test_create_access_token_includes_password_version() -> None:
    """Test that create_access_token includes password_version in token payload."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    password_version = 5

    token = create_access_token(user_id, password_version)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["password_version"] == password_version
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_default_password_version() -> None:
    """Test that create_access_token defaults to password_version=1 if not provided."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    token = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["password_version"] == 1
    assert payload["type"] == "access"


def test_create_access_token_with_custom_expires_delta() -> None:
    """Test that create_access_token respects custom expires_delta."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    password_version = 2
    custom_expiry = timedelta(hours=2)

    before_creation = datetime.now(UTC)
    token = create_access_token(user_id, password_version, custom_expiry)
    after_creation = datetime.now(UTC)

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["password_version"] == password_version
    assert payload["type"] == "access"

    # Verify expiration time is approximately 2 hours from now
    exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected_min = before_creation + custom_expiry
    expected_max = after_creation + custom_expiry
    assert expected_min <= exp_time <= expected_max


def test_create_access_token_default_expiration() -> None:
    """Test that create_access_token uses default expiration from settings."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    before_creation = datetime.now(UTC)
    token = create_access_token(user_id)
    after_creation = datetime.now(UTC)

    payload = decode_access_token(token)

    # Default expiration is 15 minutes from settings
    from app.core.config import settings

    default_expiry = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected_min = before_creation + default_expiry
    expected_max = after_creation + default_expiry
    assert expected_min <= exp_time <= expected_max


# ============== TEMP TOKEN TESTS ==============


def test_create_temp_token_no_password_version() -> None:
    """Test that create_temp_token does NOT include password_version."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    token = create_temp_token(user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert "password_version" not in payload
    assert payload["type"] == "temp"


def test_create_temp_token_expiration() -> None:
    """Test that temp token expires in 10 minutes."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"

    before_creation = datetime.now(UTC)
    token = create_temp_token(user_id)
    after_creation = datetime.now(UTC)

    payload = decode_access_token(token)

    # Temp token expires in 10 minutes
    temp_expiry = timedelta(minutes=10)

    exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected_min = before_creation + temp_expiry
    expected_max = after_creation + temp_expiry
    assert expected_min <= exp_time <= expected_max


# ============== TOKEN DECODING TESTS ==============


def test_decode_access_token_valid_token() -> None:
    """Test that decode_access_token correctly decodes valid token."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    password_version = 3

    token = create_access_token(user_id, password_version)
    payload = decode_access_token(token)

    assert isinstance(payload, dict)
    assert payload["sub"] == user_id
    assert payload["password_version"] == password_version


def test_decode_access_token_invalid_token_raises_error() -> None:
    """Test that decode_access_token raises jwt.InvalidTokenError for invalid tokens."""
    invalid_token = "invalid.token.string"

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(invalid_token)


def test_decode_access_token_malformed_token_raises_error() -> None:
    """Test that decode_access_token raises jwt.InvalidTokenError for malformed tokens."""
    malformed_token = "not-a-jwt"

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(malformed_token)
