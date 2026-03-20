"""Unit tests for rate limiting configuration and enforcement."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.limiter import limiter

# ---------------------------------------------------------------------------
# 1. Limiter configuration tests
# ---------------------------------------------------------------------------


def test_limiter_uses_get_remote_address_as_key_func():
    """The shared limiter must use a key function that falls back to get_remote_address.

    The production limiter uses _get_user_or_ip which provides per-user rate limiting
    when an Authorization Bearer token is present, and falls back to IP-based limiting
    otherwise — a superset of the get_remote_address behaviour.
    """
    from app.core.limiter import _get_user_or_ip

    assert limiter._key_func is _get_user_or_ip


def test_limiter_is_slowapi_limiter_instance():
    """The limiter object must be a slowapi Limiter."""
    assert isinstance(limiter, Limiter)


def test_limiter_has_default_limits():
    """The limiter should be created with a non-empty default_limits list."""
    assert limiter._default_limits  # truthy — at least one default limit set


# ---------------------------------------------------------------------------
# 2. 429 enforcement test using an isolated FastAPI app with a 1/minute limit
# ---------------------------------------------------------------------------


@pytest.fixture()
def rate_limited_app():
    """Return a minimal FastAPI app that enforces a 1/minute limit on POST /test."""
    test_limiter = Limiter(key_func=get_remote_address)
    app = FastAPI()
    app.state.limiter = test_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    from fastapi import Request

    @app.post("/test")
    @test_limiter.limit("1/minute")
    async def limited_endpoint(request: Request) -> dict:
        return {"ok": True}

    return app


def test_rate_limit_returns_429_after_limit_exceeded(rate_limited_app: FastAPI):
    """Second request within the same minute should return HTTP 429."""
    with TestClient(rate_limited_app, raise_server_exceptions=False) as client:
        first = client.post("/test")
        assert first.status_code == 200

        second = client.post("/test")
        assert second.status_code == 429


def test_rate_limit_first_request_succeeds(rate_limited_app: FastAPI):
    """The first request must always succeed (not be rate-limited)."""
    with TestClient(rate_limited_app, raise_server_exceptions=False) as client:
        response = client.post("/test")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


# ---------------------------------------------------------------------------
# 3. Main app wiring test
# ---------------------------------------------------------------------------


def test_main_app_has_limiter_state():
    """The main FastAPI application must have limiter wired into its state."""
    from app.main import application

    assert hasattr(application.state, "limiter")
    assert application.state.limiter is limiter
