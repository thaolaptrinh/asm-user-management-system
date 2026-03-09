import uuid
from datetime import UTC, datetime

from sqlalchemy import CHAR, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=uuid.uuid4,
        insert_default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


__all__ = ["Base", "UUIDMixin", "TimestampMixin"]
