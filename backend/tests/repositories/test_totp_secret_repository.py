"""Tests for TotpSecretRepository."""

from datetime import datetime, timezone

import pytest

from app.models.totp_secret import TotpSecret
from app.models.user import User
from app.repositories.totp_secret import TotpSecretRepository


@pytest.mark.asyncio
async def test_get_by_user_id_returns_totp_secret(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Test retrieving TOTP secret by user ID."""
    result = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))

    assert result is not None
    assert result.user_id == str(sample_user_with_totp.id)
    assert result.secret == "JBSWY3DPEHPK3PXP"
    assert result.is_verified is True


@pytest.mark.asyncio
async def test_get_by_user_id_returns_none_for_unknown(
    totp_repo: TotpSecretRepository,
):
    """Test retrieving TOTP secret for a non-existent user returns None."""
    result = await totp_repo.get_by_user_id("non-existent-user-id")
    assert result is None


@pytest.mark.asyncio
async def test_update_last_used(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Test updating last_used_at and last_used_counter."""
    counter = 1_000_000
    await totp_repo.update_last_used(str(sample_user_with_totp.id), counter)

    result = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))
    assert result is not None
    assert result.last_used_at is not None
    assert isinstance(result.last_used_at, datetime)
    assert result.last_used_counter == counter


@pytest.mark.asyncio
async def test_mark_verified_sets_flag(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Test mark_verified sets is_verified=True via direct UPDATE."""
    # First set to unverified
    totp = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))
    assert totp is not None
    totp.is_verified = False
    await totp_repo.session.flush()

    await totp_repo.mark_verified(str(sample_user_with_totp.id))

    result = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))
    assert result is not None
    assert result.is_verified is True


@pytest.mark.asyncio
async def test_check_last_used_counter_blocks_same_counter(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Replay attack: same counter value as last used should be blocked."""
    counter = 1_000_000
    await totp_repo.update_last_used(str(sample_user_with_totp.id), counter)

    result = await totp_repo.check_last_used_counter(
        str(sample_user_with_totp.id), counter
    )
    assert result is True


@pytest.mark.asyncio
async def test_check_last_used_counter_blocks_earlier_counter(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Replay attack: counter value earlier than last used should also be blocked."""
    counter = 1_000_000
    await totp_repo.update_last_used(str(sample_user_with_totp.id), counter)

    result = await totp_repo.check_last_used_counter(
        str(sample_user_with_totp.id), counter - 1
    )
    assert result is True


@pytest.mark.asyncio
async def test_check_last_used_counter_allows_newer_counter(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """New counter value (later window) should be allowed."""
    counter = 1_000_000
    await totp_repo.update_last_used(str(sample_user_with_totp.id), counter)

    result = await totp_repo.check_last_used_counter(
        str(sample_user_with_totp.id), counter + 1
    )
    assert result is False


@pytest.mark.asyncio
async def test_check_last_used_counter_without_last_used(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """No prior usage — should not block any counter."""
    totp = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))
    if totp:
        totp.last_used_at = None
        totp.last_used_counter = None
        await totp_repo.session.flush()

    result = await totp_repo.check_last_used_counter(
        str(sample_user_with_totp.id), 1_000_000
    )
    assert result is False


@pytest.mark.asyncio
async def test_create_or_update_creates_new_totp_secret(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Test create_or_update creates a new record when none exists."""
    existing = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))
    if existing:
        await totp_repo.session.delete(existing)
        await totp_repo.session.flush()

    result = await totp_repo.create_or_update(
        user_id=str(sample_user_with_totp.id),
        secret="NEWSECRET123456",
        algorithm="SHA1",
        digits=6,
        period=30,
    )
    assert result is not None
    assert isinstance(result, TotpSecret)
    assert result.secret == "NEWSECRET123456"
    assert result.is_verified is False


@pytest.mark.asyncio
async def test_create_or_update_overwrites_unverified(
    totp_repo: TotpSecretRepository, sample_user_with_totp: User
):
    """Test create_or_update overwrites existing unverified secret."""
    totp = await totp_repo.get_by_user_id(str(sample_user_with_totp.id))
    assert totp is not None
    totp.is_verified = False
    await totp_repo.session.flush()

    result = await totp_repo.create_or_update(
        user_id=str(sample_user_with_totp.id),
        secret="UPDATEDSECRET789",
    )
    assert result.secret == "UPDATEDSECRET789"
    assert result.is_verified is False
    assert result.last_used_at is None
    assert result.last_used_counter is None
