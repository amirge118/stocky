"""Add alerts table

Revision ID: 005_add_alerts
Revises: 004_add_watchlists
Create Date: 2026-03-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_add_alerts"
down_revision: Union[str, None] = "004_add_watchlists"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

conditiontype_enum = sa.Enum("ABOVE", "BELOW", "EQUAL", name="conditiontype")


def upgrade() -> None:
    # Idempotent: a failed run can leave `conditiontype` in the DB while alembic is still
    # before 005; `create_type=False` on the column does not always stop SQLAlchemy from
    # emitting CREATE TYPE again, so use a safe PG block instead of Enum.create().
    op.execute(
        """
        DO $do$
        BEGIN
            CREATE TYPE conditiontype AS ENUM ('ABOVE', 'BELOW', 'EQUAL');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $do$;
        """
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column(
            "condition_type",
            postgresql.ENUM(
                "ABOVE", "BELOW", "EQUAL",
                name="conditiontype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("target_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_triggered", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alerts_ticker", "alerts", ["ticker"])
    op.create_index("idx_alerts_is_active", "alerts", ["is_active"])
    op.create_index("idx_alerts_ticker_is_active", "alerts", ["ticker", "is_active"])


def downgrade() -> None:
    op.drop_index("idx_alerts_ticker_is_active", table_name="alerts")
    op.drop_index("idx_alerts_is_active", table_name="alerts")
    op.drop_index("idx_alerts_ticker", table_name="alerts")
    op.drop_table("alerts")
    conditiontype_enum.drop(op.get_bind(), checkfirst=True)
