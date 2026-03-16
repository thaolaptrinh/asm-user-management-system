"""Tests for RecoveryCodesService."""

import uuid

import pytest
import pytest_asyncio

from app.core.security import hash_password
from app.models.user import User
from app.repositories.totp_recovery_code import TotpRecoveryCodeRepository
from app.services.recovery_codes import RecoveryCodesService


@pytest_asyncio.fixture
async def user(session):
    u = User(
        id=uuid.uuid4(),
        email=f"rcsvc_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(u)
    await session.flush()
    return u


@pytest_asyncio.fixture
def service(session):
    repo = TotpRecoveryCodeRepository(session)
    return RecoveryCodesService(repo)


@pytest.mark.asyncio
async def test_generate_codes_returns_10(service):
    """generate_codes returns 10 formatted codes."""
    codes = service.generate_codes()
    assert len(codes) == 10
    for code in codes:
        assert len(code) == 9  # XXXX-XXXX format
        assert "-" in code


@pytest.mark.asyncio
async def test_hash_and_verify_code(service):
    """hash_code + verify_code_hash round-trip works."""
    code = "ABCD-EFGH"
    hashed = service.hash_code(code)
    assert service.verify_code_hash(code, hashed) is True
    assert service.verify_code_hash("WRONG-CODE", hashed) is False


@pytest.mark.asyncio
async def test_normalize_code(service):
    """normalize_code uppercases and strips dashes/spaces."""
    assert service.normalize_code("abcd-efgh") == "ABCDEFGH"
    assert service.normalize_code("ABCD EFGH") == "ABCDEFGH"
    assert service.normalize_code("abcd efgh") == "ABCDEFGH"


@pytest.mark.asyncio
async def test_generate_for_user(service, user):
    """generate_for_user returns 10 plaintext codes and stores hashes in DB."""
    codes = await service.generate_for_user(str(user.id))
    assert len(codes) == 10


@pytest.mark.asyncio
async def test_generate_for_user_replaces_existing(service, user):
    """Calling generate_for_user twice replaces old codes."""
    first = await service.generate_for_user(str(user.id))
    second = await service.generate_for_user(str(user.id))
    count = await service.get_remaining_count(str(user.id))
    assert count == 10  # Only 10 codes, not 20


@pytest.mark.asyncio
async def test_verify_valid_code(service, user):
    """verify returns True for a valid unused code."""
    codes = await service.generate_for_user(str(user.id))
    result = await service.verify(str(user.id), codes[0])
    assert result is True


@pytest.mark.asyncio
async def test_verify_marks_code_used(service, user):
    """verify marks code as used; second verify with same code returns False."""
    codes = await service.generate_for_user(str(user.id))
    await service.verify(str(user.id), codes[0])
    result = await service.verify(str(user.id), codes[0])
    assert result is False


@pytest.mark.asyncio
async def test_verify_wrong_code(service, user):
    """verify returns False for an incorrect code."""
    await service.generate_for_user(str(user.id))
    result = await service.verify(str(user.id), "XXXX-XXXX")
    assert result is False


@pytest.mark.asyncio
async def test_verify_wrong_length(service, user):
    """verify returns False if normalized code length != CODE_LENGTH."""
    await service.generate_for_user(str(user.id))
    result = await service.verify(str(user.id), "SHORT")
    assert result is False


@pytest.mark.asyncio
async def test_get_remaining_count(service, user):
    """get_remaining_count decreases after each verify."""
    codes = await service.generate_for_user(str(user.id))
    assert await service.get_remaining_count(str(user.id)) == 10
    await service.verify(str(user.id), codes[0])
    assert await service.get_remaining_count(str(user.id)) == 9


@pytest.mark.asyncio
async def test_regenerate(service, user):
    """regenerate replaces codes and returns 10 fresh ones."""
    await service.generate_for_user(str(user.id))
    new_codes = await service.regenerate(str(user.id))
    assert len(new_codes) == 10
    assert await service.get_remaining_count(str(user.id)) == 10
