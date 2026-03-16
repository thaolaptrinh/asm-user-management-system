"""Tests for TotpService."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.exceptions import ConflictError, UnauthorizedError
from app.services.totp import TotpService, _challenges

# A fake counter value used by tests to simulate a currently valid TOTP window.
_FAKE_COUNTER = 1_000_000


@pytest.mark.asyncio
async def test_generate_secret(totp_service: TotpService):
    """Test secret generation."""
    secret = totp_service.generate_secret()

    assert secret is not None
    assert isinstance(secret, str)
    assert len(secret) >= 16  # Base32 secrets are typically 16+ chars
    # Base32 only contains A-Z and 2-7
    assert all(c.isupper() or c in "234567" for c in secret)


@pytest.mark.asyncio
async def test_generate_qr_code(
    totp_service: TotpService, sample_user_with_totp, mock_qr_code
):
    """Test QR code generation with thread pool offloading."""
    secret = "JBSWY3DPEHPK3PXP"
    email = sample_user_with_totp.email

    # Mock qrcode generation to avoid CPU-intensive operation
    with (
        patch("app.services.totp.qrcode") as mock_qrcode,
        patch("app.services.totp.asyncio.to_thread") as mock_to_thread,
    ):
        mock_to_thread.return_value = mock_qr_code

        result = await totp_service.generate_qr_code(secret, email)

        assert result == mock_qr_code
        mock_to_thread.assert_called_once()
        # Verify the function passed to to_thread is callable
        call_args = mock_to_thread.call_args
        assert callable(call_args[0][0])


@pytest.mark.asyncio
async def test_get_otpauth_url(totp_service: TotpService, sample_user_with_totp):
    """Test OTPAuth URL generation."""
    from urllib.parse import unquote

    from app.core.config import settings

    secret = "JBSWY3DPEHPK3PXP"
    email = sample_user_with_totp.email

    url = totp_service._get_otpauth_url(secret, email)

    assert url.startswith("otpauth://totp/")
    assert secret in url
    assert email in unquote(url)
    assert settings.APP_NAME in unquote(url)


@pytest.mark.asyncio
async def test_find_accepted_counter_valid(totp_service: TotpService):
    """Test _find_accepted_counter returns the matching counter for a valid code."""
    import pyotp as _pyotp

    secret = "JBSWY3DPEHPK3PXP"
    # Generate the actual current code for this secret
    totp_obj = _pyotp.TOTP(secret)
    code = totp_obj.now()

    result = totp_service._find_accepted_counter(
        secret=secret,
        totp_code=code,
        algorithm="SHA1",
        digits=6,
        period=30,
    )
    assert result is not None
    assert isinstance(result, int)


@pytest.mark.asyncio
async def test_find_accepted_counter_invalid(totp_service: TotpService):
    """Test _find_accepted_counter returns None for an invalid code."""
    with patch("app.services.totp.pyotp.TOTP") as mock_totp_class:
        mock_totp = MagicMock()
        mock_totp.at.return_value = "999999"  # Never matches
        mock_totp_class.return_value = mock_totp

        result = totp_service._find_accepted_counter(
            secret="JBSWY3DPEHPK3PXP",
            totp_code="000000",
            algorithm="SHA1",
            digits=6,
            period=30,
        )
        assert result is None


@pytest.mark.asyncio
async def test_find_accepted_counter_sha256(totp_service: TotpService):
    """Test _find_accepted_counter uses the correct digest for SHA256."""
    import hashlib

    with patch("app.services.totp.pyotp.TOTP") as mock_totp_class:
        mock_totp = MagicMock()
        mock_totp.at.return_value = "999999"  # Never matches
        mock_totp_class.return_value = mock_totp

        totp_service._find_accepted_counter(
            secret="JBSWY3DPEHPK3PXP",
            totp_code="123456",
            algorithm="SHA256",
            digits=6,
            period=30,
        )
        call_kwargs = mock_totp_class.call_args[1]
        assert call_kwargs["digest"] is hashlib.sha256


@pytest.mark.asyncio
async def test_find_accepted_counter_sha512(totp_service: TotpService):
    """Test _find_accepted_counter uses the correct digest for SHA512."""
    import hashlib

    with patch("app.services.totp.pyotp.TOTP") as mock_totp_class:
        mock_totp = MagicMock()
        mock_totp.at.return_value = "999999"
        mock_totp_class.return_value = mock_totp

        totp_service._find_accepted_counter(
            secret="JBSWY3DPEHPK3PXP",
            totp_code="123456",
            algorithm="SHA512",
            digits=6,
            period=30,
        )
        call_kwargs = mock_totp_class.call_args[1]
        assert call_kwargs["digest"] is hashlib.sha512


@pytest.mark.asyncio
async def test_is_totp_enabled_true(totp_service: TotpService, sample_user_with_totp):
    """Test checking if TOTP is enabled (true case)."""
    result = await totp_service.is_totp_enabled(str(sample_user_with_totp.id))
    assert result is True


@pytest.mark.asyncio
async def test_is_totp_enabled_false(totp_service: TotpService):
    """Test checking if TOTP is enabled (false case - no TOTP)."""
    result = await totp_service.is_totp_enabled("nonexistent-user-id")
    assert result is False


@pytest.mark.asyncio
async def test_get_totp_status_enabled(
    totp_service: TotpService, sample_user_with_totp
):
    """Test getting TOTP status when enabled."""
    status = await totp_service.get_totp_status(str(sample_user_with_totp.id))

    assert status.is_enabled is True
    assert "is enabled" in status.message


@pytest.mark.asyncio
async def test_get_totp_status_disabled(totp_service: TotpService):
    """Test getting TOTP status when disabled."""
    status = await totp_service.get_totp_status("nonexistent-user-id")

    assert status.is_enabled is False
    assert "is not enabled" in status.message


@pytest.mark.asyncio
async def test_create_totp_for_user_new(
    totp_service: TotpService, sample_user_with_totp, mock_qr_code
):
    """Test creating TOTP for new user."""
    # Delete existing TOTP
    existing = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if existing:
        await totp_service._repo.session.delete(existing)
        await totp_service._repo.session.flush()

    with patch.object(
        totp_service, "generate_qr_code", return_value=mock_qr_code
    ) as mock_qr:
        result = await totp_service.create_totp_for_user(
            str(sample_user_with_totp.id), sample_user_with_totp.email
        )

        assert result.secret is not None
        assert result.qr_code == mock_qr_code
        assert result.otpauth_url.startswith("otpauth://totp/")
        mock_qr.assert_called_once()


@pytest.mark.asyncio
async def test_create_totp_for_user_already_verified(
    totp_service: TotpService, sample_user_with_totp
):
    """Test creating TOTP when already verified (should fail)."""
    with pytest.raises(ConflictError, match="TOTP is already enabled"):
        await totp_service.create_totp_for_user(
            str(sample_user_with_totp.id), sample_user_with_totp.email
        )


@pytest.mark.asyncio
async def test_verify_totp_for_login_success(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test TOTP verification for login with valid code."""
    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER
    ):
        result = await totp_service.verify_totp_for_login(
            str(sample_user_with_totp.id), valid_totp_code
        )

        assert result is True


@pytest.mark.asyncio
async def test_verify_totp_for_login_not_enabled(totp_service: TotpService):
    """Test TOTP verification for login when TOTP not enabled."""
    with pytest.raises(UnauthorizedError, match="TOTP secret does not exist"):
        await totp_service.verify_totp_for_login("nonexistent-user-id", "123456")


@pytest.mark.asyncio
async def test_verify_totp_for_login_replay_attack(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test TOTP verification blocks replay of an already-used counter."""
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.last_used_counter = _FAKE_COUNTER
        await totp_service._repo.session.flush()

    # _find_accepted_counter returns the same counter that was already stored
    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER
    ):
        with pytest.raises(UnauthorizedError, match="already used in current window"):
            await totp_service.verify_totp_for_login(
                str(sample_user_with_totp.id), valid_totp_code
            )


@pytest.mark.asyncio
async def test_verify_totp_for_login_replay_attack_adjacent_window(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test that a code from an adjacent window is blocked if its counter was already used."""
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        # last used counter is _FAKE_COUNTER; attacker tries to replay with counter-1
        totp.last_used_counter = _FAKE_COUNTER
        await totp_service._repo.session.flush()

    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER - 1
    ):
        with pytest.raises(UnauthorizedError, match="already used in current window"):
            await totp_service.verify_totp_for_login(
                str(sample_user_with_totp.id), valid_totp_code
            )


@pytest.mark.asyncio
async def test_verify_totp_for_login_invalid_code(
    totp_service: TotpService, sample_user_with_totp
):
    """Test TOTP verification with invalid code."""
    with patch.object(totp_service, "_find_accepted_counter", return_value=None):
        with pytest.raises(UnauthorizedError, match="Invalid TOTP code"):
            await totp_service.verify_totp_for_login(
                str(sample_user_with_totp.id), "000000"
            )


@pytest.mark.asyncio
async def test_verify_totp_for_enrollment_success(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test TOTP verification for enrollment with valid code."""
    # Make TOTP unverified
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.is_verified = False
        await totp_service._repo.session.flush()

    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER
    ):
        result = await totp_service.verify_totp_for_enrollment(
            str(sample_user_with_totp.id), valid_totp_code
        )

        assert result is True

        # Verify TOTP is now marked as verified
        updated_totp = await totp_service._repo.get_by_user_id(
            str(sample_user_with_totp.id)
        )
        assert updated_totp.is_verified is True


@pytest.mark.asyncio
async def test_verify_totp_for_enrollment_no_secret(totp_service: TotpService):
    """Test TOTP verification for enrollment without secret."""
    with pytest.raises(UnauthorizedError, match="TOTP secret does not exist"):
        await totp_service.verify_totp_for_enrollment("nonexistent-user-id", "123456")


@pytest.mark.asyncio
async def test_verify_totp_for_enrollment_already_verified(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test TOTP verification for enrollment when already verified."""
    with pytest.raises(ConflictError, match="TOTP is already enabled"):
        await totp_service.verify_totp_for_enrollment(
            str(sample_user_with_totp.id), valid_totp_code
        )


@pytest.mark.asyncio
async def test_verify_totp_for_enrollment_replay_attack(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test TOTP verification for enrollment with replay attack."""
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.is_verified = False
        totp.last_used_counter = _FAKE_COUNTER
        await totp_service._repo.session.flush()

    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER
    ):
        with pytest.raises(UnauthorizedError, match="already used in current window"):
            await totp_service.verify_totp_for_enrollment(
                str(sample_user_with_totp.id), valid_totp_code
            )


@pytest.mark.asyncio
async def test_verify_totp_common_replay_check(
    totp_service: TotpService, sample_user_with_totp, valid_totp_code
):
    """Test common replay attack prevention logic."""
    # Test with check_verified=True, mark_as_verified=False (login flow)
    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER
    ):
        result = await totp_service._verify_totp_with_replay_check(
            user_id=str(sample_user_with_totp.id),
            totp_code=valid_totp_code,
            check_verified=True,
            mark_as_verified=False,
        )
        assert result is True

    # Test with check_verified=False, mark_as_verified=True (enrollment flow)
    totp = await totp_service._repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.is_verified = False
        totp.last_used_counter = None  # reset so replay check doesn't block
        await totp_service._repo.session.flush()

    with patch.object(
        totp_service, "_find_accepted_counter", return_value=_FAKE_COUNTER + 1
    ):
        result = await totp_service._verify_totp_with_replay_check(
            user_id=str(sample_user_with_totp.id),
            totp_code=valid_totp_code,
            check_verified=False,
            mark_as_verified=True,
        )
        assert result is True

        # Verify TOTP is now marked as verified
        updated_totp = await totp_service._repo.get_by_user_id(
            str(sample_user_with_totp.id)
        )
        assert updated_totp.is_verified is True


# ── Challenge tests ────────────────────────────────────────────────────────────


def test_create_challenge_returns_valid_response(
    totp_service: TotpService, sample_user_with_totp
):
    """Test create_challenge returns a valid TotpChallengeResponse."""
    user_id = str(sample_user_with_totp.id)
    response = totp_service.create_challenge(user_id)

    assert response.challenge_id is not None
    assert isinstance(response.challenge_id, uuid.UUID)
    assert response.expires_in == 60


def test_create_challenge_stores_in_memory(
    totp_service: TotpService, sample_user_with_totp
):
    """Test that create_challenge stores entry in the in-memory dict."""
    _challenges.clear()
    user_id = str(sample_user_with_totp.id)
    response = totp_service.create_challenge(user_id)

    challenge_key = str(response.challenge_id)
    assert challenge_key in _challenges
    assert _challenges[challenge_key]["user_id"] == user_id
    assert "expires_at" in _challenges[challenge_key]
    _challenges.clear()


def test_resolve_challenge_returns_user_id(
    totp_service: TotpService, sample_user_with_totp
):
    """Test resolve_challenge returns correct user_id and consumes the entry."""
    _challenges.clear()
    user_id = str(sample_user_with_totp.id)
    response = totp_service.create_challenge(user_id)

    resolved = totp_service.resolve_challenge(str(response.challenge_id))

    assert resolved == user_id
    # Challenge must be consumed (single-use)
    assert str(response.challenge_id) not in _challenges
    _challenges.clear()


def test_resolve_challenge_raises_for_unknown_id(totp_service: TotpService):
    """Test resolve_challenge raises UnauthorizedError for unknown challenge_id."""
    with pytest.raises(UnauthorizedError, match="Invalid or expired challenge"):
        totp_service.resolve_challenge(str(uuid.uuid4()))


def test_resolve_challenge_raises_for_expired(
    totp_service: TotpService, sample_user_with_totp
):
    """Test resolve_challenge raises UnauthorizedError for an expired challenge."""
    _challenges.clear()
    challenge_id = str(uuid.uuid4())
    _challenges[challenge_id] = {
        "user_id": str(sample_user_with_totp.id),
        "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
    }

    with pytest.raises(UnauthorizedError, match="Invalid or expired challenge"):
        totp_service.resolve_challenge(challenge_id)

    _challenges.clear()


def test_purge_expired_challenges(totp_service: TotpService, sample_user_with_totp):
    """Test _purge_expired_challenges removes only expired entries."""
    _challenges.clear()
    now = datetime.now(timezone.utc)
    _challenges["expired"] = {
        "user_id": "u1",
        "expires_at": now - timedelta(seconds=10),
    }
    _challenges["valid"] = {
        "user_id": "u2",
        "expires_at": now + timedelta(seconds=60),
    }

    totp_service._purge_expired_challenges()

    assert "expired" not in _challenges
    assert "valid" in _challenges
    _challenges.clear()
