"""Add whatsapp_enabled and whatsapp_phone to notification_settings

Revision ID: 009_add_whatsapp_settings
Revises: 008_add_notification_settings
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_add_whatsapp_settings"
down_revision: Union[str, None] = "008_add_notification_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notification_settings",
        sa.Column(
            "whatsapp_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "notification_settings",
        sa.Column("whatsapp_phone", sa.String(32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("notification_settings", "whatsapp_phone")
    op.drop_column("notification_settings", "whatsapp_enabled")
