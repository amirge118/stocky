"""Unit tests for app/core/yf_utils.py — _is_rate_limited and _is_retryable."""

from app.core.yf_utils import _is_rate_limited, _is_retryable


# ---------------------------------------------------------------------------
# _is_rate_limited
# ---------------------------------------------------------------------------


def test_is_rate_limited_with_429():
    assert _is_rate_limited(Exception("HTTP 429")) is True


def test_is_rate_limited_with_too_many_requests():
    assert _is_rate_limited(Exception("Too Many Requests")) is True


def test_is_rate_limited_with_rate_limit():
    assert _is_rate_limited(Exception("rate limit exceeded")) is True


def test_is_rate_limited_with_ratelimit():
    assert _is_rate_limited(Exception("ratelimit hit")) is True


def test_is_rate_limited_generic_error():
    assert _is_rate_limited(Exception("connection refused")) is False


# ---------------------------------------------------------------------------
# _is_retryable
# ---------------------------------------------------------------------------


def test_is_retryable_rate_limited():
    # Delegates to _is_rate_limited — "429" substring triggers True
    assert _is_retryable(Exception("429")) is True


def test_is_retryable_timeout():
    assert _is_retryable(Exception("timeout occurred")) is True


def test_is_retryable_connection():
    assert _is_retryable(Exception("connection error")) is True


def test_is_retryable_temporary():
    assert _is_retryable(Exception("temporarily unavailable")) is True


def test_is_retryable_eof():
    assert _is_retryable(Exception("unexpected EOF")) is True


def test_is_retryable_network():
    assert _is_retryable(Exception("network error")) is True


def test_is_retryable_generic_error():
    assert _is_retryable(Exception("permission denied")) is False
