import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User


def generate_password_reset_token(email: str) -> str:
    """Generate a JWT-based password reset token (expires in 1 hour)."""
    now = datetime.now(UTC)
    payload = {
        "exp": now + timedelta(hours=1),
        "iat": now,
        "sub": email,
        "type": "password_reset",
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_password_reset_token(token: str) -> str | None:
    """Verify a password reset token and return the email, or None if invalid."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


async def create_user_password_reset_token(
    session: AsyncSession, email: str
) -> str | None:
    """Create password reset token and save it in database."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None

    token = generate_password_reset_token(email)
    user.reset_token = token
    user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    await session.flush()

    return token


async def verify_password_reset_token_and_get_user(
    session: AsyncSession, token: str
) -> User | None:
    """Verify password reset token and return user if valid."""
    email = verify_password_reset_token(token)
    if not email:
        return None

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.reset_token or user.reset_token != token:
        return None

    if user.reset_token_expires:
        expires = user.reset_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            return None

    return user


async def delete_password_reset_token(session: AsyncSession, user: User) -> None:
    """Clear password reset token from database."""
    user.reset_token = None
    user.reset_token_expires = None
    await session.flush()


def send_email(email_to: str, subject: str, body: str) -> None:
    """Send email using configured SMTP. Prints to console if SMTP is disabled."""
    if settings.mail_enabled:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_ADDRESS}>"
        msg["To"] = email_to

        with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=10) as server:
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
    else:
        print(f"[MOCK EMAIL] To: {email_to}, Subject: {subject}")
