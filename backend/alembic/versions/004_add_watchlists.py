"""Add watchlist_lists and watchlist_items tables

Revision ID: 004_add_watchlists
Revises: 003_add_agent_reports
Create Date: 2026-03-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_watchlists"
down_revision: Union[str, None] = "003_add_agent_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "watchlist_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_watchlist_lists_position", "watchlist_lists", ["position"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "watchlist_id",
            sa.Integer(),
            sa.ForeignKey("watchlist_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_item"),
    )
    op.create_index("idx_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"])
    op.create_index("idx_watchlist_items_symbol", "watchlist_items", ["symbol"])


def downgrade() -> None:
    op.drop_index("idx_watchlist_items_symbol", table_name="watchlist_items")
    op.drop_index("idx_watchlist_items_watchlist_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index("idx_watchlist_lists_position", table_name="watchlist_lists")
    op.drop_table("watchlist_lists")
