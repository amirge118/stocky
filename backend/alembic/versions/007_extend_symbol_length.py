"""Extend symbol/ticker columns from String(10) to String(15) to support TASE symbols (e.g. BEZQ.TA)

Revision ID: 007_extend_symbol_length
Revises: 006_add_purchase_date
Create Date: 2026-03-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_extend_symbol_length"
down_revision: Union[str, None] = "006_add_purchase_date"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "stocks", "symbol",
        type_=sa.String(15),
        existing_type=sa.String(10),
        existing_nullable=False,
    )
    op.alter_column(
        "holdings", "symbol",
        type_=sa.String(15),
        existing_type=sa.String(10),
        existing_nullable=False,
    )
    op.alter_column(
        "alerts", "ticker",
        type_=sa.String(15),
        existing_type=sa.String(10),
        existing_nullable=False,
    )
    op.alter_column(
        "watchlist_items", "symbol",
        type_=sa.String(15),
        existing_type=sa.String(10),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "watchlist_items", "symbol",
        type_=sa.String(10),
        existing_type=sa.String(15),
        existing_nullable=False,
    )
    op.alter_column(
        "alerts", "ticker",
        type_=sa.String(10),
        existing_type=sa.String(15),
        existing_nullable=False,
    )
    op.alter_column(
        "holdings", "symbol",
        type_=sa.String(10),
        existing_type=sa.String(15),
        existing_nullable=False,
    )
    op.alter_column(
        "stocks", "symbol",
        type_=sa.String(10),
        existing_type=sa.String(15),
        existing_nullable=False,
    )
