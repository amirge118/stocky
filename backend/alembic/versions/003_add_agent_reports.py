"""Add agent_reports table

Revision ID: 003_add_agent_reports
Revises: 002_add_holdings
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "003_add_agent_reports"
down_revision: Union[str, None] = "002_add_holdings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("target_symbol", sa.String(10), nullable=True),
        sa.Column("data", JSONB, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("run_duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agent_reports_agent_name", "agent_reports", ["agent_name"])
    op.create_index("idx_agent_reports_agent_type", "agent_reports", ["agent_type"])
    op.create_index("idx_agent_reports_target_symbol", "agent_reports", ["target_symbol"])
    op.create_index(
        "idx_agent_reports_name_symbol_created",
        "agent_reports",
        ["agent_name", "target_symbol", "created_at"],
    )
    op.create_index(
        "idx_agent_reports_type_created",
        "agent_reports",
        ["agent_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_agent_reports_type_created", table_name="agent_reports")
    op.drop_index("idx_agent_reports_name_symbol_created", table_name="agent_reports")
    op.drop_index("idx_agent_reports_target_symbol", table_name="agent_reports")
    op.drop_index("idx_agent_reports_agent_type", table_name="agent_reports")
    op.drop_index("idx_agent_reports_agent_name", table_name="agent_reports")
    op.drop_table("agent_reports")
