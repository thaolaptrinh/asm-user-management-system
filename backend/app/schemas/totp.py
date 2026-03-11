import uuid

from pydantic import BaseModel, Field, model_validator


class LoginTempTokenResponse(BaseModel):
    """Response for POST /auth/login — step 1 of 2FA flow."""

    temp_token: str = Field(..., description="Short-lived token for TOTP verification")
    message: str = Field(default="Please enter TOTP code")


class TotpStatusResponse(BaseModel):
    """Response for GET /auth/totp/status"""

    is_enabled: bool
    message: str


class TotpEnrollResponse(BaseModel):
    """Response for POST /auth/totp/enroll"""

    secret: str = Field(..., description="Base32 encoded secret")
    qr_code: str = Field(..., description="Base64 encoded PNG QR code")
    otpauth_url: str = Field(..., description="OTPAuth URL for authenticator apps")


class TotpChallengeResponse(BaseModel):
    """Response for POST /auth/totp/challenge"""

    challenge_id: uuid.UUID = Field(
        ..., description="Unique challenge ID for enrollment"
    )
    expires_in: int = Field(..., description="Seconds until challenge expires")


class TotpVerifyRequest(BaseModel):
    """
    Combined request for POST /auth/totp/verify.
    Flow A (login):    provide temp_token + totp_code
    Flow B (enroll):   provide challenge_id + totp_code
    """

    temp_token: str | None = Field(None, description="Flow A: temp token from login")
    challenge_id: uuid.UUID | None = Field(
        None, description="Flow B: challenge ID from /auth/totp/challenge"
    )
    totp_code: str = Field(
        ..., min_length=6, max_length=8, description="TOTP code from authenticator"
    )

    @model_validator(mode="after")
    def validate_flow(self) -> "TotpVerifyRequest":
        has_temp = self.temp_token is not None
        has_challenge = self.challenge_id is not None
        # Flow A: temp_token only (no challenge_id)
        # Flow B: challenge_id required; temp_token is optional (binding check)
        if not has_temp and not has_challenge:
            raise ValueError("Either temp_token or challenge_id must be provided")
        if has_temp and not has_challenge:
            return self  # Flow A
        if has_challenge:
            return self  # Flow B (temp_token may or may not be present)
        return self

    @property
    def is_flow_a(self) -> bool:
        """Flow A: temp_token present and no challenge_id."""
        return self.temp_token is not None and self.challenge_id is None


class TotpVerifyFlowAResponse(BaseModel):
    """Response for successful TOTP verification (Flow A — login)"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: dict = Field(..., description="User information")


class TotpVerifyFlowBResponse(BaseModel):
    """Response for successful TOTP enrollment (Flow B — enroll confirm)"""

    message: str = Field(
        default="TOTP is enabled", description="Success message"
    )
    is_enabled: bool = Field(default=True, description="TOTP enabled status")
    recovery_codes: list[str] = Field(
        default_factory=list,
        description="Plaintext recovery codes generated after enrollment. Shown ONCE — user must save them.",
    )
