from pydantic import BaseModel, Field


class RecoveryCodesGenerateResponse(BaseModel):
    codes: list[str] = Field(
        ..., description="Recovery codes (plaintext returned ONLY on generation)"
    )
    remaining_count: int = Field(..., description="Number of remaining unused codes")
    message: str = Field(
        default="Save these codes in a safe place - you will not be able to view them again"
    )


class RecoveryCodesStatusResponse(BaseModel):
    remaining_count: int = Field(..., description="Number of remaining unused codes")
    message: str = Field(..., description="Status message")


class RecoveryVerifyRequest(BaseModel):
    code: str = Field(
        ..., min_length=9, max_length=9, description="Recovery code (format: XXXX-XXXX)"
    )
    temp_token: str | None = Field(
        None, description="Temp token from login (for verification during login)"
    )


class RecoveryVerifyResponse(BaseModel):
    remaining_count: int = Field(..., description="Number of remaining unused codes")
    message: str = Field(..., description="Result message")
    access_token: str | None = Field(
        None, description="JWT access token (returned only on successful login via recovery code)"
    )
