"""
Test user service password change functionality.
"""

import pytest

from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import verify_password
from app.schemas.user import ChangePassword


@pytest.mark.asyncio
async def test_change_password_success(user_service, normal_user, audit_repo):
    """Test successful password change increments version."""
    old_version = normal_user.password_version
    data = ChangePassword(
        current_password="TestPassword123!",
        new_password="NewPassword456!"
    )

    await user_service.change_password(
        normal_user,
        data,
        ip_address="127.0.0.1",
        user_agent="test-agent",
        audit_repo=audit_repo
    )

    # Verify password changed
    assert verify_password("NewPassword456!", normal_user.hashed_password)
    assert normal_user.password_version == old_version + 1


@pytest.mark.asyncio
async def test_change_password_wrong_current_password(user_service, normal_user, audit_repo):
    """Test change password fails with wrong current password."""
    data = ChangePassword(
        current_password="WrongPassword",
        new_password="NewPassword456!"
    )

    with pytest.raises(UnauthorizedError, match="Current password is incorrect"):
        await user_service.change_password(
            normal_user,
            data,
            ip_address="127.0.0.1",
            user_agent="test-agent",
            audit_repo=audit_repo
        )


@pytest.mark.asyncio
async def test_change_password_prevents_reuse(user_service, normal_user, audit_repo):
    """Test password change prevents immediate reuse (caught by schema)."""
    from pydantic import ValidationError as PydanticValidationError

    # Schema validation catches reuse before service call
    with pytest.raises(PydanticValidationError, match="must be different"):
        ChangePassword(
            current_password="TestPassword123!",
            new_password="TestPassword123!"
        )


@pytest.mark.asyncio
async def test_change_password_invalidates_tokens(user_service, normal_user):
    """Test password change invalidates existing tokens."""
    from app.core.security import create_access_token, decode_access_token

    # Create token with old password version
    old_token = create_access_token(
        str(normal_user.id),
        password_version=normal_user.password_version
    )

    # Change password
    data = ChangePassword(
        current_password="TestPassword123!",
        new_password="NewPassword456!"
    )
    from app.repositories.audit_log import AuditLogRepository
    await user_service.change_password(normal_user, data, audit_repo=None)

    # Old token should have wrong version
    payload = decode_access_token(old_token)
    assert payload["password_version"] != normal_user.password_version
