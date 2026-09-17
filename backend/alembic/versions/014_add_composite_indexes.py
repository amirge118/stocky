"""Add composite indexes for common query patterns.

Revision ID: 014_add_composite_indexes
Revises: 013_enable_rls_transactions
Create Date: 2026-09-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "014_add_composite_indexes"
down_revision: Union[str, None] = "013_enable_rls_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # holdings: (symbol, purchase_date) — date-range queries per symbol
    op.create_index(
        "idx_holdings_symbol_purchase_date",
        "holdings",
        ["symbol", "purchase_date"],
        if_not_exists=True,
    )

    # alerts: (ticker, condition_type) — group/filter alerts by type per ticker
    op.create_index(
        "idx_alerts_ticker_condition_type",
        "alerts",
        ["ticker", "condition_type"],
        if_not_exists=True,
    )

    # watchlist_items: (watchlist_id, position) — ordered listing within a watchlist
    op.create_index(
        "idx_watchlist_items_watchlist_id_position",
        "watchlist_items",
        ["watchlist_id", "position"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("idx_watchlist_items_watchlist_id_position", table_name="watchlist_items")
    op.drop_index("idx_alerts_ticker_condition_type", table_name="alerts")
    op.drop_index("idx_holdings_symbol_purchase_date", table_name="holdings")
