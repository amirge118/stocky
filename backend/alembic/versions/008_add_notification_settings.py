"""Add notification_settings table

Revision ID: 008_add_notification_settings
Revises: 007_extend_symbol_length
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_add_notification_settings"
down_revision: Union[str, None] = "007_extend_symbol_length"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "telegram_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("telegram_chat_id", sa.String(64), nullable=True),
        sa.Column(
            "browser_push_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 1", name="notification_settings_singleton"),
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
