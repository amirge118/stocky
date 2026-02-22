"""Add stock model

Revision ID: 001_initial_stock_model
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_stock_model'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stocks table
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('exchange', sa.String(length=50), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_stocks_symbol', 'stocks', ['symbol'], unique=True)
    op.create_index('idx_stocks_exchange', 'stocks', ['exchange'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_stocks_exchange', table_name='stocks')
    op.drop_index('idx_stocks_symbol', table_name='stocks')
    
    # Drop table
    op.drop_table('stocks')
