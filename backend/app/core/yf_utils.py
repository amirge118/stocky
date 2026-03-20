"""Reliability helpers for yfinance: rate-limit detection and retry decorator."""

import logging
from typing import Any, cast

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def _is_rate_limited(exc: BaseException) -> bool:
    """Return True when Yahoo Finance is throttling us (HTTP 429 or equivalent)."""
    s = str(exc).lower()
    return (
        "429" in s
        or "too many requests" in s
        or "rate limit" in s
        or "ratelimit" in s
    )


def _is_retryable(exc: BaseException) -> bool:
    """Return True for transient errors that warrant an automatic retry."""
    if _is_rate_limited(exc):
        return True
    s = str(exc).lower()
    return any(
        kw in s
        for kw in ("timeout", "timed out", "connection", "temporarily", "reset", "eof", "network")
    )


# Decorate blocking sync functions that call yfinance.
# Runs inside executor threads so time.sleep in the wait is fine.
yf_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
    before_sleep=before_sleep_log(cast(Any, logger), logging.WARNING),
)
