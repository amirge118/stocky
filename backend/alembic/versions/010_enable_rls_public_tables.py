"""Enable Row Level Security on public tables (Supabase Security Advisor).

Revision ID: 010_enable_rls_public_tables
Revises: 009_add_whatsapp_settings
Create Date: 2026-04-02

PostgREST/anon cannot access these tables without policies. The FastAPI backend
uses the database owner role and bypasses RLS (PostgreSQL default for table owners).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "010_enable_rls_public_tables"
down_revision: Union[str, None] = "009_add_whatsapp_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables flagged by Supabase "RLS Disabled in Public" (schema public).
_RLS_TABLES = (
    "alembic_version",
    "stocks",
    "agent_reports",
    "watchlist_lists",
    "watchlist_items",
    "alerts",
    "holdings",
    "notification_settings",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    for name in _RLS_TABLES:
        op.execute(f'ALTER TABLE public."{name}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    for name in _RLS_TABLES:
        op.execute(f'ALTER TABLE public."{name}" DISABLE ROW LEVEL SECURITY')
