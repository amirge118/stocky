"""Add purchase_date to holdings

Revision ID: 006_add_purchase_date
Revises: 005_add_alerts
Create Date: 2026-03-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_add_purchase_date"
down_revision: Union[str, None] = "005_add_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "holdings",
        sa.Column(
            "purchase_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
    )


def downgrade() -> None:
    op.drop_column("holdings", "purchase_date")
