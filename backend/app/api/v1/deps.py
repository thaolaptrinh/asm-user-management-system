from typing import Annotated

import uuid

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.totp_recovery_code import TotpRecoveryCodeRepository
from app.repositories.totp_secret import TotpSecretRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.recovery_codes import RecoveryCodesService
from app.services.totp import TotpService
from app.services.user import UserService

# auto_error=False so we can handle missing token ourselves (check cookie first)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_totp_repo(session: SessionDep) -> TotpSecretRepository:
    return TotpSecretRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
TotpRepoDep = Annotated[TotpSecretRepository, Depends(get_totp_repo)]


def get_audit_log_repo(session: SessionDep) -> AuditLogRepository:
    """Get audit log repository."""
    return AuditLogRepository(session)


AuditLogRepositoryDep = Annotated[AuditLogRepository, Depends(get_audit_log_repo)]


def get_auth_service(user_repo: UserRepoDep) -> AuthService:
    return AuthService(user_repo)


def get_user_service(user_repo: UserRepoDep) -> UserService:
    return UserService(user_repo)


def get_totp_service(totp_repo: TotpRepoDep) -> TotpService:
    return TotpService(totp_repo)


def get_recovery_codes_repo(session: SessionDep) -> TotpRecoveryCodeRepository:
    return TotpRecoveryCodeRepository(session)


RecoveryCodesRepoDep = Annotated[
    TotpRecoveryCodeRepository, Depends(get_recovery_codes_repo)
]


def get_recovery_codes_service(
    recovery_codes_repo: RecoveryCodesRepoDep,
) -> RecoveryCodesService:
    return RecoveryCodesService(recovery_codes_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TotpServiceDep = Annotated[TotpService, Depends(get_totp_service)]
RecoveryCodesServiceDep = Annotated[
    RecoveryCodesService, Depends(get_recovery_codes_service)
]


def _extract_token(
    request: Request,
    bearer: Annotated[str | None, Depends(oauth2_scheme)],
) -> str:
    """Read token from HttpOnly cookie first, then Authorization header as fallback."""
    token = request.cookies.get("access_token")
    if token:
        return token
    if bearer:
        return bearer
    raise UnauthorizedError()


TokenDep = Annotated[str, Depends(_extract_token)]


async def get_current_user(token: TokenDep, user_repo: UserRepoDep) -> User:
    """Dependency for fully-authenticated endpoints. Rejects temp tokens."""
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError()
        user_id: str = str(payload["sub"])
    except (InvalidTokenError, KeyError):
        raise UnauthorizedError()

    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    # Validate password_version
    password_version_value = payload.get("password_version", 0)
    token_password_version = (
        int(password_version_value)
        if isinstance(password_version_value, (int, str, float))
        else 0
    )
    if user.password_version != token_password_version:
        raise UnauthorizedError(
            "Your session has been invalidated. Please log in again."
        )

    return user


async def get_totp_authorized_user(token: TokenDep, user_repo: UserRepoDep) -> User:
    """Dependency for TOTP endpoints — accepts both access_token and temp_token."""
    try:
        payload = decode_access_token(token)
        if payload.get("type") not in ("access", "temp"):
            raise UnauthorizedError()
        user_id: str = str(payload["sub"])
    except (InvalidTokenError, KeyError):
        raise UnauthorizedError()

    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
TotpAuthorizedUser = Annotated[User, Depends(get_totp_authorized_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise ForbiddenError("Superuser access required")
    return current_user


SuperuserDep = Annotated[User, Depends(get_current_superuser)]
