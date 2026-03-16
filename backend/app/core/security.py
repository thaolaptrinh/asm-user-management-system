from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

JWT_TEMP_TOKEN_EXPIRE_MINUTES = 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    subject: str, password_version: int = 1, expires_delta: timedelta | None = None
) -> str:
    delta = expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + delta
    payload = {
        "sub": subject,
        "password_version": password_version,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_temp_token(subject: str) -> str:
    """Issue a short-lived (10 min) token scoped only for TOTP endpoints."""
    expire = datetime.now(UTC) + timedelta(minutes=JWT_TEMP_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "temp",
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict[str, object]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
