import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None


class UserUpdateMe(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)


class UserPublic(UserBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserResetPasswordToken(BaseModel):
    """Schema for password reset token validation."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePassword(BaseModel):
    """Schema for password change."""
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str, info: ValidationInfo) -> str:
        """Prevent password reuse and weak passwords."""
        if 'current_password' in info.data and v == info.data['current_password']:
            raise ValueError('New password must be different from current password')

        weak_passwords = ['password', '12345678', 'qwerty123', 'abc12345']
        if v.lower() in weak_passwords:
            raise ValueError('Password is too common')

        return v


class Message(BaseModel):
    message: str
