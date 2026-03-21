"""Unit tests for app/core/cache.py — in-memory path only (no Redis)."""

import time
from unittest.mock import patch

import pytest

import app.core.cache as cache_module
from app.core.cache import (
    MAX_MEMORY_ENTRIES,
    cache_delete,
    cache_get,
    cache_set,
)


@pytest.fixture(autouse=True)
def reset_cache_globals():
    """Reset module-level globals before every test so state never leaks."""
    cache_module._memory_cache.clear()
    cache_module._redis_client = None
    cache_module._redis_unavailable = False
    yield
    cache_module._memory_cache.clear()
    cache_module._redis_client = None
    cache_module._redis_unavailable = False


@pytest.fixture(autouse=True)
def no_redis(reset_cache_globals):
    """Patch settings so Redis is never attempted."""
    with patch("app.core.cache.settings") as mock_settings:
        mock_settings.redis_url = None
        yield mock_settings


# ── cache_get ────────────────────────────────────────────────────────────────


async def test_cache_get_missing_key_returns_none():
    result = await cache_get("nonexistent")
    assert result is None


# ── cache_set / cache_get round-trip ─────────────────────────────────────────


async def test_cache_set_then_get_returns_value():
    await cache_set("mykey", {"data": 42}, ttl=60)
    result = await cache_get("mykey")
    assert result == {"data": 42}


# ── TTL expiry ────────────────────────────────────────────────────────────────


async def test_cache_get_returns_none_after_ttl_expiry():
    """Setting TTL=0 means expires_at == now; mocking time forward makes it expired."""
    await cache_set("expiring", "value", ttl=0)
    # Advance time so the entry is considered expired
    with patch("app.core.cache.time") as mock_time:
        mock_time.time.return_value = time.time() + 1
        result = await cache_get("expiring")
    assert result is None


# ── cache_delete ─────────────────────────────────────────────────────────────


async def test_cache_delete_removes_key():
    await cache_set("to_delete", "bye", ttl=60)
    await cache_delete("to_delete")
    result = await cache_get("to_delete")
    assert result is None


# ── eviction ─────────────────────────────────────────────────────────────────


async def test_eviction_removes_oldest_expiry_entry():
    """Fill to MAX_MEMORY_ENTRIES; adding one more must evict the entry with the
    smallest (earliest) expires_at value."""
    base_time = time.time()

    # Populate cache directly so we control exact expires_at values.
    # Entry "oldest_key" gets the smallest expires_at and must be evicted.
    cache_module._memory_cache["oldest_key"] = ("oldest_value", base_time + 1)
    for i in range(MAX_MEMORY_ENTRIES - 1):
        cache_module._memory_cache[f"key_{i}"] = ("v", base_time + 1000 + i)

    assert len(cache_module._memory_cache) == MAX_MEMORY_ENTRIES

    # Adding one more entry should trigger eviction of "oldest_key"
    await cache_set("new_key", "new_value", ttl=9999)

    assert len(cache_module._memory_cache) == MAX_MEMORY_ENTRIES
    assert "oldest_key" not in cache_module._memory_cache
    assert "new_key" in cache_module._memory_cache


# ── Redis exception falls back to memory ─────────────────────────────────────


async def test_cache_get_falls_back_to_memory_on_redis_exception():
    """When _get_redis() returns a client whose .get() raises, we read from memory."""
    # Pre-populate the memory cache directly
    cache_module._memory_cache["fallback_key"] = ("mem_value", time.time() + 60)

    # Build a fake Redis client whose get() raises
    from unittest.mock import AsyncMock, MagicMock

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(side_effect=Exception("Redis down"))
    cache_module._redis_client = fake_redis
    # Also make settings.redis_url truthy so _get_redis() returns the fake client
    with patch("app.core.cache.settings") as mock_settings:
        mock_settings.redis_url = "redis://localhost:6379"
        result = await cache_get("fallback_key")

    assert result == "mem_value"
