"""Unit tests for private helper functions in health.py."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.endpoints.health import _check_database, _check_redis
from app.schemas.common import HealthCheck


# ── _check_database ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_database_success():
    """_check_database returns HealthCheck(status='ok') when engine connects."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_ctx

    # engine is imported inside the function from app.core.database, so patch there
    with patch("app.core.database.engine", mock_engine):
        result = await _check_database()

    assert isinstance(result, HealthCheck)
    assert result.status == "ok"
    assert result.detail is None


@pytest.mark.asyncio
async def test_check_database_failure():
    """_check_database returns HealthCheck(status='error') when engine raises."""
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(side_effect=Exception("db error"))
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_ctx

    with patch("app.core.database.engine", mock_engine):
        result = await _check_database()

    assert isinstance(result, HealthCheck)
    assert result.status == "error"
    assert result.detail is not None
    assert "db error" in result.detail


# ── _check_redis ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_redis_none_returns_fallback():
    """_check_redis returns in-memory fallback HealthCheck when _get_redis() is None."""
    # _get_redis is imported inside the function from app.core.cache, so patch there
    with patch("app.core.cache._get_redis", return_value=None):
        result = await _check_redis()

    assert isinstance(result, HealthCheck)
    assert result.status == "ok"
    assert result.detail == "in-memory fallback"


@pytest.mark.asyncio
async def test_check_redis_success():
    """_check_redis returns HealthCheck(status='ok') when ping succeeds."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    with patch("app.core.cache._get_redis", return_value=mock_redis):
        result = await _check_redis()

    assert isinstance(result, HealthCheck)
    assert result.status == "ok"
    assert result.detail is None


@pytest.mark.asyncio
async def test_check_redis_failure():
    """_check_redis returns HealthCheck(status='error') when ping raises."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("redis error"))

    with patch("app.core.cache._get_redis", return_value=mock_redis):
        result = await _check_redis()

    assert isinstance(result, HealthCheck)
    assert result.status == "error"
    assert result.detail is not None
    assert "redis error" in result.detail
