from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.v1.deps import AuthServiceDep, SessionDep, UserServiceDep
from app.core.config import settings
from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.schemas.common import Message
from app.schemas.user import UserCreate, UserRegister, UserResetPasswordToken
from app.utils import (
    create_user_password_reset_token,
    delete_password_reset_token,
    send_email,
    verify_password_reset_token_and_get_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

_COOKIE_NAME = "access_token"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/")


@router.post("/login", response_model=Message, operation_id="login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
) -> Message:
    user = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )
    token = auth_service.issue_token(user)
    _set_auth_cookie(response, token)
    return Message(message="Login successful")


@router.post("/logout", response_model=Message, operation_id="logout")
async def logout(response: Response) -> Message:
    _clear_auth_cookie(response)
    return Message(message="Logout successful")


@router.post(
    "/register", response_model=Message, status_code=201, operation_id="register"
)
async def register(
    response: Response,
    user_data: UserRegister,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
) -> Message:
    """Register a new user, set auth cookie, and return success message."""
    user = await user_service.create(
        UserCreate(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
    )
    token = auth_service.issue_token(user)
    _set_auth_cookie(response, token)
    return Message(message="Registration successful")


@router.post(
    "/password-recovery/{email}", response_model=Message, operation_id="recoverPassword"
)
@limiter.limit("5/minute")
async def recover_password(
    email: str,
    request: Request,
    session: SessionDep,
) -> Message:
    """Request password recovery email (anti-enumeration: always returns success)."""
    token = await create_user_password_reset_token(session, email)

    if token:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        body = (
            f"You requested a password reset.\n\n"
            f"Use this link to reset your password:\n{reset_url}\n\n"
            f"If you did not request this, please ignore this email."
        )
        try:
            send_email(email_to=email, subject="Password Recovery", body=body)
        except Exception:
            pass  # Silently fail to prevent email enumeration

    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password/", response_model=Message, operation_id="resetPassword")
async def reset_password(
    data: UserResetPasswordToken,
    session: SessionDep,
) -> Message:
    """Reset password with valid token."""
    user = await verify_password_reset_token_and_get_user(session, data.token)
    if not user:
        raise ConflictError("Invalid or expired reset token")

    user.hashed_password = hash_password(data.new_password)
    await delete_password_reset_token(session, user)

    return Message(message="Password updated successfully")
