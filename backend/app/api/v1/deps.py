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
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.item import ItemService

# auto_error=False so we can handle missing token ourselves (check cookie first)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_item_repo(session: SessionDep) -> ItemRepository:
    return ItemRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
ItemRepoDep = Annotated[ItemRepository, Depends(get_item_repo)]


def get_auth_service(user_repo: UserRepoDep) -> AuthService:
    return AuthService(user_repo)


def get_user_service(user_repo: UserRepoDep) -> UserService:
    return UserService(user_repo)


def get_item_service(item_repo: ItemRepoDep) -> ItemService:
    return ItemService(item_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


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
    try:
        payload = decode_access_token(token)
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


async def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise ForbiddenError("Superuser access required")
    return current_user


SuperuserDep = Annotated[User, Depends(get_current_superuser)]
