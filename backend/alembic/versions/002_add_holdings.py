"""Add holdings table

Revision ID: 002_add_holdings
Revises: 001_initial_stock_model
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_holdings'
down_revision: Union[str, None] = '001_initial_stock_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('shares', sa.Float(), nullable=False),
        sa.Column('avg_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_holdings_symbol', 'holdings', ['symbol'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_holdings_symbol', table_name='holdings')
    op.drop_table('holdings')
