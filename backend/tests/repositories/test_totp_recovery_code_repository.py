"""Tests for TotpRecoveryCodeRepository."""

import uuid

import pytest
import pytest_asyncio

from app.models.totp_recovery_code import TotpRecoveryCode
from app.models.user import User
from app.core.security import hash_password
from app.repositories.totp_recovery_code import TotpRecoveryCodeRepository


@pytest_asyncio.fixture
async def user(session):
    u = User(
        id=uuid.uuid4(),
        email=f"rc_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("Password123"),
        is_active=True,
        is_superuser=False,
    )
    session.add(u)
    await session.flush()
    return u


@pytest_asyncio.fixture
async def repo(session):
    return TotpRecoveryCodeRepository(session)


@pytest.mark.asyncio
async def test_create_batch_and_get_by_user_id(repo, user):
    """create_batch stores codes; get_by_user_id returns them all."""
    hashes = ["hash1", "hash2", "hash3"]
    created = await repo.create_batch(str(user.id), hashes)
    assert len(created) == 3

    codes = await repo.get_by_user_id(str(user.id))
    assert len(codes) == 3


@pytest.mark.asyncio
async def test_get_by_user_id_empty(repo, user):
    """get_by_user_id returns empty list when no codes exist."""
    codes = await repo.get_by_user_id(str(user.id))
    assert codes == []


@pytest.mark.asyncio
async def test_get_unused_by_user_id(repo, user):
    """get_unused_by_user_id returns only codes where used_at is None."""
    await repo.create_batch(str(user.id), ["hash_a", "hash_b"])
    unused = await repo.get_unused_by_user_id(str(user.id))
    assert len(unused) == 2


@pytest.mark.asyncio
async def test_verify_and_mark_used_success(repo, user):
    """verify_and_mark_used returns True and marks the code used."""
    await repo.create_batch(str(user.id), ["myhash"])
    result = await repo.verify_and_mark_used(str(user.id), "myhash")
    assert result is True

    # Code is now used — should not appear in unused list
    unused = await repo.get_unused_by_user_id(str(user.id))
    assert len(unused) == 0


@pytest.mark.asyncio
async def test_verify_and_mark_used_not_found(repo, user):
    """verify_and_mark_used returns False for unknown code hash."""
    result = await repo.verify_and_mark_used(str(user.id), "nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_verify_and_mark_used_already_used(repo, user):
    """verify_and_mark_used returns False if code already used."""
    await repo.create_batch(str(user.id), ["usedhash"])
    await repo.verify_and_mark_used(str(user.id), "usedhash")
    # Try to use the same code again
    result = await repo.verify_and_mark_used(str(user.id), "usedhash")
    assert result is False


@pytest.mark.asyncio
async def test_get_remaining_count(repo, user):
    """get_remaining_count returns count of unused codes."""
    await repo.create_batch(str(user.id), ["h1", "h2", "h3"])
    count = await repo.get_remaining_count(str(user.id))
    assert count == 3

    await repo.verify_and_mark_used(str(user.id), "h1")
    count = await repo.get_remaining_count(str(user.id))
    assert count == 2


@pytest.mark.asyncio
async def test_get_remaining_count_zero(repo, user):
    """get_remaining_count returns 0 when no codes exist."""
    count = await repo.get_remaining_count(str(user.id))
    assert count == 0


@pytest.mark.asyncio
async def test_delete_all(repo, user):
    """delete_all removes all codes for a user."""
    await repo.create_batch(str(user.id), ["h1", "h2"])
    await repo.delete_all(str(user.id))
    codes = await repo.get_by_user_id(str(user.id))
    assert codes == []


@pytest.mark.asyncio
async def test_get_by_user_id_and_code_hash_found(repo, user):
    """get_by_user_id_and_code_hash returns matching code."""
    await repo.create_batch(str(user.id), ["targethash"])
    code = await repo.get_by_user_id_and_code_hash(str(user.id), "targethash")
    assert code is not None
    assert code.code_hash == "targethash"


@pytest.mark.asyncio
async def test_get_by_user_id_and_code_hash_not_found(repo, user):
    """get_by_user_id_and_code_hash returns None when not found."""
    code = await repo.get_by_user_id_and_code_hash(str(user.id), "missing")
    assert code is None
