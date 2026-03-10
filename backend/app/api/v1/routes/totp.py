import uuid

from fastapi import APIRouter, Request, Response
from jwt import InvalidTokenError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.v1.cookie import set_auth_cookie
from app.api.v1.deps import (
    RecoveryCodesServiceDep,
    TotpAuthorizedUser,
    TotpServiceDep,
    UserRepoDep,
)
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, decode_access_token
from app.schemas.totp import (
    TotpChallengeResponse,
    TotpEnrollResponse,
    TotpStatusResponse,
    TotpVerifyFlowAResponse,
    TotpVerifyFlowBResponse,
    TotpVerifyRequest,
)

router = APIRouter(prefix="/auth/totp", tags=["totp"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/status", response_model=TotpStatusResponse, operation_id="totpStatus")
async def get_totp_status(
    current_user: TotpAuthorizedUser,
    totp_service: TotpServiceDep,
) -> TotpStatusResponse:
    """Check whether the current user has TOTP enabled."""
    return await totp_service.get_totp_status(str(current_user.id))


@router.post("/enroll", response_model=TotpEnrollResponse, operation_id="totpEnroll")
async def enroll_totp(
    current_user: TotpAuthorizedUser,
    totp_service: TotpServiceDep,
) -> TotpEnrollResponse:
    """
    Step 1 of enrollment: generate secret + QR code.
    Returns 409 if TOTP is already active.
    """
    return await totp_service.create_totp_for_user(
        str(current_user.id), current_user.email
    )


@router.post(
    "/challenge", response_model=TotpChallengeResponse, operation_id="totpChallenge"
)
async def create_totp_challenge(
    current_user: TotpAuthorizedUser,
    totp_service: TotpServiceDep,
) -> TotpChallengeResponse:
    """
    Step 2 of enrollment: create an in-memory challenge (TTL 60s).
    Use the returned challenge_id in the verify endpoint (Flow B).
    """
    return totp_service.create_challenge(str(current_user.id))


@router.post(
    "/verify",
    operation_id="totpVerify",
)
@limiter.limit("10/minute")
async def verify_totp(
    request: Request,
    body: TotpVerifyRequest,
    response: Response,
    totp_service: TotpServiceDep,
    user_repo: UserRepoDep,
    recovery_codes_service: RecoveryCodesServiceDep,
) -> TotpVerifyFlowAResponse | TotpVerifyFlowBResponse:
    """
    Dual-purpose TOTP verify endpoint.

    Flow A (login — send temp_token + totp_code):
      Validates temp_token, verifies TOTP code, sets access_token cookie, returns access_token.

    Flow B (enrollment confirm — send challenge_id + totp_code):
      Resolves challenge to user, verifies TOTP, marks secret as verified.
      Optionally accepts temp_token to bind enrollment to the current login session.
      Auto-generates recovery codes and returns them (shown once — user must save).
      Client must then call Flow A to obtain an access_token.
    """
    if body.is_flow_a:
        return await _handle_flow_a(body, totp_service, user_repo, response)
    return await _handle_flow_b(body, totp_service, recovery_codes_service)


async def _handle_flow_a(
    body: TotpVerifyRequest,
    totp_service: TotpServiceDep,
    user_repo: UserRepoDep,
    response: Response,
) -> TotpVerifyFlowAResponse:
    """Flow A: temp_token + totp_code → access_token (set as HttpOnly cookie)."""
    try:
        payload = decode_access_token(body.temp_token)  # type: ignore[arg-type]
        if payload.get("type") != "temp":
            raise UnauthorizedError("Token không hợp lệ")
        user_id = str(payload["sub"])
    except (InvalidTokenError, KeyError):
        raise UnauthorizedError("Token không hợp lệ hoặc đã hết hạn")

    await totp_service.verify_totp_for_login(user_id, body.totp_code)

    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise UnauthorizedError("User not found")

    access_token = create_access_token(user_id)
    set_auth_cookie(response, access_token)
    return TotpVerifyFlowAResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_superuser": user.is_superuser,
        },
    )


async def _handle_flow_b(
    body: TotpVerifyRequest,
    totp_service: TotpServiceDep,
    recovery_codes_service: RecoveryCodesServiceDep,
) -> TotpVerifyFlowBResponse:
    """Flow B: challenge_id + totp_code → TOTP activated + recovery codes generated."""
    user_id = totp_service.resolve_challenge(str(body.challenge_id))

    # If temp_token was also provided (login enrollment flow), verify it matches the
    # challenge's user to prevent cross-session enrollment.
    if body.temp_token:
        try:
            payload = decode_access_token(body.temp_token)
            if payload.get("type") != "temp" or str(payload["sub"]) != user_id:
                raise UnauthorizedError("Token không hợp lệ")
        except (InvalidTokenError, KeyError):
            raise UnauthorizedError("Token không hợp lệ hoặc đã hết hạn")

    await totp_service.verify_totp_for_enrollment(user_id, body.totp_code)
    recovery_codes = await recovery_codes_service.generate_for_user(user_id)
    return TotpVerifyFlowBResponse(recovery_codes=recovery_codes)
