from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CHAR, DateTime, ForeignKey, String
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class TotpSecret(TimestampMixin, Base):
    """TOTP secret for each user (1-1 relationship with users table)."""

    __tablename__ = "totp_secrets"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(10), default="SHA1", nullable=False)
    digits: Mapped[int] = mapped_column(TINYINT, default=6, nullable=False)
    period: Mapped[int] = mapped_column(TINYINT, default=30, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_counter: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
