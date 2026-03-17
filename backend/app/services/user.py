import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import ChangePassword, UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def create(self, data: UserCreate) -> User:
        if await self._repo.email_exists(data.email):
            raise ConflictError("The user with this email already exists in the system")
        return await self._repo.create(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_active=True,
            is_superuser=False,
        )

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.email and data.email != user.email:
            if await self._repo.email_exists(data.email):
                raise ConflictError(
                    "The user with this email already exists in the system"
                )

        update_kwargs: dict[str, object] = data.model_dump(
            exclude_unset=True, exclude={"password"}
        )
        if data.password:
            update_kwargs["hashed_password"] = hash_password(data.password)

        return await self._repo.update(user, **update_kwargs)

    async def get_or_404(self, user_id: object) -> User:
        user = await self._repo.get_by_id(uuid.UUID(str(user_id)))
        if user is None:
            raise NotFoundError("User", None)
        return user

    async def change_password(
        self,
        user: User,
        data: ChangePassword,
        ip_address: str | None = None,
        user_agent: str | None = None,
        audit_repo: Any | None = None,
    ) -> None:
        """Change user password with security best practices."""

        # 1. Verify current password
        if not verify_password(data.current_password, user.hashed_password):
            if audit_repo:
                await audit_repo.create(
                    user_id=str(user.id),
                    action="PASSWORD_CHANGE_FAILED",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="FAILED",
                    meta={"reason": "invalid_current_password"},
                )
            raise UnauthorizedError("Current password is incorrect")

        # 2. Check password reuse
        if verify_password(data.new_password, user.hashed_password):
            if audit_repo:
                await audit_repo.create(
                    user_id=str(user.id),
                    action="PASSWORD_CHANGE_FAILED",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="FAILED",
                    meta={"reason": "password_reuse"},
                )
            raise ValidationError(
                "New password must be different from current password"
            )

        # 3. Update password and increment version
        new_hashed = hash_password(data.new_password)
        new_version = user.password_version + 1

        await self._repo.update(
            user, hashed_password=new_hashed, password_version=new_version
        )

        # 4. Log successful password change
        if audit_repo:
            await audit_repo.create(
                user_id=str(user.id),
                action="PASSWORD_CHANGED",
                ip_address=ip_address,
                user_agent=user_agent,
                status="SUCCESS",
                meta={"password_version": new_version},
            )

        # 5. Send email notification
        from app.utils import send_email

        try:
            body = (
                f"Your password was successfully changed.\n\n"
                f"If you did not make this change, please contact support immediately.\n\n"
                f"Time: {datetime.now(UTC).isoformat()}\n"
                f"IP: {ip_address}\n"
            )
            send_email(email_to=user.email, subject="Password Changed", body=body)
        except Exception:
            pass  # Silently fail
