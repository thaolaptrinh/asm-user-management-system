import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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


class Message(BaseModel):
    message: str
