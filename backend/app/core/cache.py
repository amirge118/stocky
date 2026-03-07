"""Redis-backed cache with in-memory fallback.

Redis is initialized once at first use. If it's unreachable, we fall back to
an in-memory dict for the remainder of the process lifetime (no repeated retries).
The in-memory fallback is bounded to MAX_MEMORY_ENTRIES to prevent unbounded growth.
"""
import json
import logging
import time
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback: key -> (value, expires_at)
_memory_cache: dict[str, tuple[Any, float]] = {}
MAX_MEMORY_ENTRIES = 500

_redis_client: Any = None
_redis_unavailable = False  # set True on first connection failure; stops retry loops


def _get_redis() -> Optional[Any]:
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable, using in-memory cache: %s", exc)
        _redis_unavailable = True
        return None


def _memory_set(key: str, value: Any, expires_at: float) -> None:
    """Write to in-memory cache, evicting oldest entries when at capacity."""
    if len(_memory_cache) >= MAX_MEMORY_ENTRIES and key not in _memory_cache:
        # Evict the entry with the earliest expiry
        oldest = min(_memory_cache, key=lambda k: _memory_cache[k][1])
        del _memory_cache[oldest]
    _memory_cache[key] = (value, expires_at)


async def cache_get(key: str) -> Optional[Any]:
    r = _get_redis()
    if r:
        try:
            raw = await r.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.debug("Redis get failed for %s: %s", key, exc)

    entry = _memory_cache.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        del _memory_cache[key]
        return None
    return value


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = _get_redis()
    if r:
        try:
            await r.setex(key, ttl, json.dumps(value))
            return
        except Exception as exc:
            logger.debug("Redis set failed for %s: %s", key, exc)

    _memory_set(key, value, time.time() + ttl)


async def cache_delete(key: str) -> None:
    r = _get_redis()
    if r:
        try:
            await r.delete(key)
        except Exception as exc:
            logger.debug("Redis delete failed for %s: %s", key, exc)

    _memory_cache.pop(key, None)
