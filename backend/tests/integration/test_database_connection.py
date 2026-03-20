"""
Live Postgres connectivity checks using DATABASE_URL from the environment.

Skipped automatically when DATABASE_URL is unset or not asyncpg (e.g. CI without DB).

Run locally:
  cd backend && pytest tests/integration/test_database_connection.py -v
"""

from __future__ import annotations

from urllib.parse import urlparse

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import _asyncpg_connect_args, effective_database_url


def _skip_reason() -> str | None:
    url = (settings.database_url or "").strip()
    if not url:
        return "DATABASE_URL is empty — set it in backend/.env"
    if not url.startswith("postgresql+asyncpg://"):
        return (
            "DATABASE_URL must use the asyncpg driver, e.g. "
            "postgresql+asyncpg://user:pass@host:5432/dbname "
            f"(got scheme from: {url.split('://', 1)[0]}://...)"
        )
    return None


def test_database_url_shape() -> None:
    """Host and database path are present (no raw password in assertion messages)."""
    reason = _skip_reason()
    if reason:
        pytest.skip(reason)

    url = settings.database_url.strip()
    parsed = urlparse(url.replace("postgresql+asyncpg", "http", 1))

    assert parsed.hostname, "DATABASE_URL must include a hostname"
    assert parsed.path and len(parsed.path) > 1, (
        "DATABASE_URL must include a database name after the host (e.g. /postgres)"
    )


@pytest.mark.asyncio
async def test_database_connect_and_select_one() -> None:
    """Opens a connection with the same SSL rules as the app and runs SELECT 1."""
    reason = _skip_reason()
    if reason:
        pytest.skip(reason)

    url = effective_database_url().strip()
    connect_args = _asyncpg_connect_args(url)

    engine = create_async_engine(
        url,
        echo=False,
        connect_args=connect_args,
    )
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()
