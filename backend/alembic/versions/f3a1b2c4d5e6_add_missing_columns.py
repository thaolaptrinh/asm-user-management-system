"""add_missing_columns

Revision ID: f3a1b2c4d5e6
Revises: a704f5ffc865
Create Date: 2026-03-08 08:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1b2c4d5e6"
down_revision: str | Sequence[str] | None = "a704f5ffc865"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing columns to users table."""
    # Add reset_token and reset_token_expires to users
    op.add_column("users", sa.Column("reset_token", sa.String(255), nullable=True))
    op.add_column(
        "users",
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Revert missing columns."""
    op.drop_column("users", "reset_token_expires")
    op.drop_column("users", "reset_token")
