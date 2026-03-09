"""add_missing_columns

Revision ID: f3a1b2c4d5e6
Revises: c40dcf85998e
Create Date: 2026-03-08 08:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1b2c4d5e6"
down_revision: str | Sequence[str] | None = "c40dcf85998e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing columns to users and items tables."""
    # Add reset_token and reset_token_expires to users
    op.add_column("users", sa.Column("reset_token", sa.String(255), nullable=True))
    op.add_column(
        "users",
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
    )

    # Add updated_at to items
    op.add_column(
        "items",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )

    # Fix description column type from VARCHAR(255) to TEXT
    op.alter_column(
        "items",
        "description",
        existing_type=sa.String(255),
        type_=sa.Text(),
        existing_nullable=True,
    )

    # Add index on items.title (defined in model)
    op.create_index(op.f("ix_items_title"), "items", ["title"], unique=False)

    # Add index on items.owner_id (defined in model)
    op.create_index(op.f("ix_items_owner_id"), "items", ["owner_id"], unique=False)


def downgrade() -> None:
    """Revert missing columns."""
    op.drop_index(op.f("ix_items_owner_id"), table_name="items")
    op.drop_index(op.f("ix_items_title"), table_name="items")
    op.alter_column(
        "items",
        "description",
        existing_type=sa.Text(),
        type_=sa.String(255),
        existing_nullable=True,
    )
    op.drop_column("items", "updated_at")
    op.drop_column("users", "reset_token_expires")
    op.drop_column("users", "reset_token")
