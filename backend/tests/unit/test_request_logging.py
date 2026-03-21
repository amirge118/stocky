"""Unit tests for app/middleware/request_logging.py.

Covers the pure helper functions (_redact, _safe_payload) and the
RequestLoggingMiddleware dispatch via a minimal FastAPI app.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.middleware.request_logging import RequestLoggingMiddleware, _redact, _safe_payload


# ---------------------------------------------------------------------------
# _redact
# ---------------------------------------------------------------------------


def test_redact_replaces_sensitive_key():
    """A flat dict with a sensitive key has its value replaced with '***'."""
    result = _redact({"password": "s3cr3t", "username": "alice"})
    assert result == {"password": "***", "username": "alice"}


def test_redact_leaves_non_sensitive_key_unchanged():
    """Non-sensitive keys are passed through unchanged."""
    result = _redact({"ticker": "AAPL", "price": 123.45})
    assert result == {"ticker": "AAPL", "price": 123.45}


def test_redact_all_sensitive_keys():
    """Every key in SENSITIVE_KEYS is redacted."""
    payload = {
        "password": "pw",
        "token": "tok",
        "secret": "sec",
        "api_key": "key",
        "authorization": "Bearer xyz",
        "cookie": "session=abc",
    }
    result = _redact(payload)
    for k in payload:
        assert result[k] == "***", f"Expected '***' for key '{k}'"


def test_redact_nested_dict():
    """Sensitive keys nested inside dicts are recursively redacted."""
    payload = {"user": {"password": "hidden", "name": "bob"}}
    result = _redact(payload)
    assert result == {"user": {"password": "***", "name": "bob"}}


def test_redact_list_containing_dicts():
    """Dicts inside a list are recursively redacted."""
    payload = [{"password": "pw1"}, {"token": "t1", "value": 42}]
    result = _redact(payload)
    assert result == [{"password": "***"}, {"token": "***", "value": 42}]


def test_redact_non_dict_non_list_returns_unchanged():
    """Scalar values are returned as-is."""
    assert _redact(42) == 42
    assert _redact("hello") == "hello"
    assert _redact(3.14) == 3.14
    assert _redact(None) is None


def test_redact_case_insensitive_key_matching():
    """Key matching is case-insensitive (PASSWORD vs password)."""
    result = _redact({"PASSWORD": "pw", "Token": "tok"})
    assert result["PASSWORD"] == "***"
    assert result["Token"] == "***"


# ---------------------------------------------------------------------------
# _safe_payload
# ---------------------------------------------------------------------------


def test_safe_payload_valid_json_bytes_returns_redacted_json():
    """Valid JSON bytes are parsed, redacted, and returned as a JSON string."""
    raw = b'{"username": "alice", "password": "secret"}'
    result = _safe_payload(raw)
    import json
    data = json.loads(result)
    assert data["password"] == "***"
    assert data["username"] == "alice"


def test_safe_payload_empty_bytes_returns_empty_object():
    """Empty bytes input returns '{}'."""
    assert _safe_payload(b"") == "{}"


def test_safe_payload_whitespace_only_bytes_returns_empty_object():
    """Bytes containing only whitespace are treated as empty."""
    assert _safe_payload(b"   ") == "{}"


def test_safe_payload_non_json_text_returns_as_is():
    """Non-JSON text is returned verbatim (no crash, no truncation below limit)."""
    raw = b"plain text that is not JSON"
    result = _safe_payload(raw)
    assert result == "plain text that is not JSON"


def test_safe_payload_truncates_long_payload():
    """Payloads longer than log_payload_max_length are truncated."""
    max_len = 50
    long_text = "x" * (max_len + 100)
    raw = long_text.encode()
    with patch("app.middleware.request_logging.settings") as mock_settings:
        mock_settings.log_payload_max_length = max_len
        result = _safe_payload(raw)
    assert result.endswith("... [truncated]")
    assert len(result) == max_len + len("... [truncated]")


def test_safe_payload_does_not_truncate_short_payload():
    """Payloads shorter than the limit are returned without the truncation suffix."""
    raw = b'{"key": "value"}'
    result = _safe_payload(raw)
    assert "... [truncated]" not in result


def test_safe_payload_valid_json_string_input():
    """String input (not bytes) is also handled correctly."""
    raw = '{"token": "abc123"}'
    result = _safe_payload(raw)
    import json
    data = json.loads(result)
    assert data["token"] == "***"


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware — dispatch integration
# ---------------------------------------------------------------------------


@pytest.fixture()
def logged_app():
    """Return a minimal FastAPI app with RequestLoggingMiddleware attached."""
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    async def ping() -> dict:
        return {"pong": True}

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    return app


def test_middleware_adds_x_request_id_header(logged_app: FastAPI):
    """Every response must carry an X-Request-ID header."""
    with TestClient(logged_app) as client:
        response = client.get("/ping")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 12  # uuid4().hex[:12]


def test_middleware_adds_server_timing_header(logged_app: FastAPI):
    """Every response must carry a Server-Timing header."""
    with TestClient(logged_app) as client:
        response = client.get("/ping")
    assert "server-timing" in response.headers
    assert response.headers["server-timing"].startswith("total;dur=")


def test_middleware_request_id_is_unique_per_request(logged_app: FastAPI):
    """Each request gets its own unique request ID."""
    with TestClient(logged_app) as client:
        r1 = client.get("/ping")
        r2 = client.get("/ping")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


def test_middleware_post_request_succeeds(logged_app: FastAPI):
    """POST requests (which trigger body buffering) succeed end-to-end."""
    with TestClient(logged_app) as client:
        response = client.post("/echo", json={"hello": "world"})
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}
    assert "x-request-id" in response.headers
    assert "server-timing" in response.headers
