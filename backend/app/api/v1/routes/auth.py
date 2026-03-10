from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.v1.cookie import clear_auth_cookie
from app.api.v1.deps import AuthServiceDep, SessionDep, UserServiceDep
from app.core.config import settings
from app.core.exceptions import ConflictError
from app.core.security import create_temp_token, hash_password
from app.schemas.common import Message
from app.schemas.totp import LoginTempTokenResponse
from app.schemas.user import UserCreate, UserRegister, UserResetPasswordToken
from app.utils import (
    create_user_password_reset_token,
    delete_password_reset_token,
    send_email,
    verify_password_reset_token_and_get_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=LoginTempTokenResponse, operation_id="login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
) -> LoginTempTokenResponse:
    """Step 1 of 2FA: verify email/password, return short-lived temp_token."""
    user = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )
    temp_token = create_temp_token(str(user.id))
    return LoginTempTokenResponse(temp_token=temp_token)


@router.post("/logout", response_model=Message, operation_id="logout")
async def logout(response: Response) -> Message:
    clear_auth_cookie(response)
    return Message(message="Đăng xuất thành công")


@router.post(
    "/register",
    response_model=Message,
    status_code=201,
    operation_id="register",
    responses={409: {"description": "Email already registered", "model": Message}},
)
async def register(
    user_data: UserRegister,
    user_service: UserServiceDep,
) -> Message:
    """Register a new user. Client must then go through the TOTP enroll flow."""
    await user_service.create(
        UserCreate(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
    )
    return Message(message="Đăng ký thành công. Vui lòng đăng nhập và kích hoạt TOTP.")


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
