"""Add transactions table and backfill existing holdings as BUY transactions.

Revision ID: 012_add_transactions_table
Revises: 011_drop_agent_reports
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_add_transactions_table"
down_revision: Union[str, None] = "011_drop_agent_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("symbol", sa.String(15), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("shares", sa.Float(), nullable=False),
        sa.Column("price_per_share", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("realized_gain", sa.Float(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_transactions_symbol", "transactions", ["symbol"])
    op.create_index("idx_transactions_type", "transactions", ["type"])
    op.create_index("idx_transactions_date", "transactions", ["transaction_date"])

    # Backfill: create a BUY transaction for each existing holding
    connection = op.get_bind()
    holdings = connection.execute(
        sa.text("SELECT symbol, shares, avg_cost, total_cost, purchase_date FROM holdings")
    ).fetchall()

    for row in holdings:
        symbol, shares, avg_cost, total_cost, purchase_date = row
        connection.execute(
            sa.text(
                "INSERT INTO transactions "
                "(symbol, type, shares, price_per_share, total_amount, realized_gain, transaction_date) "
                "VALUES (:symbol, 'BUY', :shares, :price_per_share, :total_amount, NULL, :transaction_date)"
            ),
            {
                "symbol": symbol,
                "shares": shares,
                "price_per_share": avg_cost,
                "total_amount": total_cost,
                "transaction_date": purchase_date,
            },
        )


def downgrade() -> None:
    op.drop_index("idx_transactions_date", table_name="transactions")
    op.drop_index("idx_transactions_type", table_name="transactions")
    op.drop_index("idx_transactions_symbol", table_name="transactions")
    op.drop_table("transactions")
