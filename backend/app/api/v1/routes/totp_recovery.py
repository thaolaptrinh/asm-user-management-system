import uuid

from fastapi import APIRouter, Request, Response

from app.api.v1.cookie import set_auth_cookie
from app.api.v1.deps import (
    RecoveryCodesServiceDep,
    RecoveryCodesRepoDep,
    TotpAuthorizedUser,
    UserRepoDep,
)
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, decode_access_token
from app.schemas.totp_recovery import (
    RecoveryCodesGenerateResponse,
    RecoveryCodesStatusResponse,
    RecoveryVerifyRequest,
    RecoveryVerifyResponse,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth/totp/recovery", tags=["totp-recovery"])

limiter = Limiter(key_func=get_remote_address)


@router.get(
    "",
    response_model=RecoveryCodesStatusResponse,
    operation_id="getRecoveryCodesStatus",
)
async def get_recovery_codes_status(
    current_user: TotpAuthorizedUser,
    recovery_codes_service: RecoveryCodesServiceDep,
) -> RecoveryCodesStatusResponse:
    """
    Get remaining recovery codes count.
    Note: Plaintext codes are NOT returned - only count.
    """
    remaining = await recovery_codes_service.get_remaining_count(str(current_user.id))
    return RecoveryCodesStatusResponse(
        remaining_count=remaining,
        message=f"{remaining} codes remaining",
    )


@router.post(
    "",
    response_model=RecoveryCodesGenerateResponse,
    operation_id="generateRecoveryCodes",
)
async def generate_recovery_codes(
    current_user: TotpAuthorizedUser,
    recovery_codes_service: RecoveryCodesServiceDep,
) -> RecoveryCodesGenerateResponse:
    """
    Generate new recovery codes.
    WARNING: Plaintext codes are returned ONLY on generation - user must save them now.
    This will invalidate all existing recovery codes.
    """
    codes = await recovery_codes_service.regenerate(str(current_user.id))
    remaining = await recovery_codes_service.get_remaining_count(str(current_user.id))

    return RecoveryCodesGenerateResponse(
        codes=codes,
        remaining_count=remaining,
        message="Save these codes in a safe place - you will not be able to view them again",
    )


@router.post(
    "/verify",
    response_model=RecoveryVerifyResponse,
    operation_id="verifyRecoveryCode",
)
@limiter.limit("10/minute")
async def verify_recovery_code(
    request: Request,
    body: RecoveryVerifyRequest,
    response: Response,
    recovery_codes_service: RecoveryCodesServiceDep,
    recovery_codes_repo: RecoveryCodesRepoDep,
    user_repo: UserRepoDep,
) -> RecoveryVerifyResponse:
    """
    Verify a recovery code (used for login when TOTP device is unavailable).
    The code will be marked as used after successful verification.
    On success, sets an HttpOnly access_token cookie and returns the access token.
    Raises 401 on invalid or already-used code.
    """
    user_id = None
    if body.temp_token:
        try:
            payload = decode_access_token(body.temp_token)
            if payload.get("type") != "temp":
                raise UnauthorizedError("Invalid token")
            user_id = str(payload["sub"])
        except Exception:
            raise UnauthorizedError("Invalid or expired token")

    if not user_id:
        raise UnauthorizedError("Temp token is required")

    is_valid = await recovery_codes_service.verify(user_id, body.code)

    if not is_valid:
        raise UnauthorizedError("Invalid or already used recovery code")

    remaining = await recovery_codes_service.get_remaining_count(user_id)
    access_token = create_access_token(user_id)
    set_auth_cookie(response, access_token)
    return RecoveryVerifyResponse(
        access_token=access_token,
        remaining_count=remaining,
        message="Valid recovery code",
    )
