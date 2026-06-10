"""Enable Row Level Security on transactions table.

Revision ID: 013_enable_rls_transactions
Revises: 012_add_transactions_table
Create Date: 2026-06-10

transactions was added after migration 010 ran, so it missed the bulk RLS enable.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "013_enable_rls_transactions"
down_revision: Union[str, None] = "012_add_transactions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    op.execute('ALTER TABLE public."transactions" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    op.execute('ALTER TABLE public."transactions" DISABLE ROW LEVEL SECURITY')
