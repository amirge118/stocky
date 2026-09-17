"""Redis-backed cache with in-memory fallback.

Redis is initialized once at first use. If it's unreachable, we fall back to
an in-memory dict for the remainder of the process lifetime (no repeated retries).
The in-memory fallback is bounded to MAX_MEMORY_ENTRIES to prevent unbounded growth.
"""

import functools
import json
import logging
import time
from typing import Any, Optional, Union

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


async def invalidate_pattern(prefix: str) -> int:
    """Delete all keys matching ``prefix*``.

    Returns the number of keys removed. Uses ``SCAN`` to avoid blocking Redis.
    In the in-memory fallback, iterates the dict directly.
    """
    count = 0
    r = _get_redis()
    if r is not None:
        try:
            cursor: Union[int, bytes] = 0
            while True:
                cursor, keys = await r.scan(
                    cursor=cursor, match=f"{prefix}*", count=200
                )
                if keys:
                    count += await r.delete(*keys)
                if cursor == 0:
                    break
            return count
        except Exception as exc:
            logger.debug("Redis SCAN/DELETE failed for prefix %s: %s", prefix, exc)

    to_delete = [k for k in _memory_cache if k.startswith(prefix)]
    for k in to_delete:
        del _memory_cache[k]
    return len(to_delete)


def cached(ttl: int = 300, prefix: Optional[str] = None):
    """Decorator that caches the return value of an async function.

    Parameters
    ----------
    ttl : int
        Time-to-live in seconds (default 300 = 5 min).
    prefix : Optional[str]
        Optional key prefix. When omitted the fully-qualified function name is used.

    Key generation: ``<prefix>:<arg0>:<arg1>:...``
    """

    def decorator(fn):
        key_prefix = prefix or f"{fn.__module__}.{fn.__qualname__}"

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            parts = [key_prefix]
            parts.extend(str(a) for a in args)
            parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(parts)

            hit = await cache_get(cache_key)
            if hit is not None:
                return hit

            result = await fn(*args, **kwargs)

            if result is not None:
                await cache_set(cache_key, result, ttl=ttl)

            return result

        wrapper.cache_prefix = key_prefix  # type: ignore[attr-defined]
        return wrapper

    return decorator
