"""Request/response logging middleware with payload support."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Union

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = frozenset(
    {"password", "token", "secret", "api_key", "authorization", "cookie"}
)


def _redact(obj: object) -> object:
    """Recursively redact sensitive keys in dict/list structures."""
    if isinstance(obj, dict):
        return {
            k: "***" if k.lower() in SENSITIVE_KEYS else _redact(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(item) for item in obj]
    return obj


def _safe_payload(raw: Union[bytes, str]) -> str:
    """Parse, redact, and truncate payload for logging."""
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    except Exception:
        return "<binary or invalid encoding>"
    if not text or not text.strip():
        return "{}"
    try:
        parsed = json.loads(text)
        redacted = _redact(parsed)
        out = json.dumps(redacted, ensure_ascii=False)
    except json.JSONDecodeError:
        out = text
    max_len = settings.log_payload_max_length
    if len(out) > max_len:
        return out[:max_len] + "... [truncated]"
    return out


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request/response with method, path, status, duration, and payloads."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        # Read request body for methods that typically have one
        request_body = b""
        if method in ("POST", "PUT", "PATCH"):
            request_body = await request.body()

            async def receive() -> dict:
                return {"type": "http.request", "body": request_body, "more_body": False}

            request = Request(request.scope, receive)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Capture response body
        response_body = b""
        if hasattr(response, "body_iterator"):
            response_body = b"".join([chunk async for chunk in response.body_iterator])
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=getattr(response, "media_type", None),
            )
        elif hasattr(response, "body"):
            response_body = response.body

        # Log level by status
        status = response.status_code
        if status < 400:
            log_level = logging.INFO
        elif status < 500:
            log_level = logging.WARNING
        else:
            log_level = logging.ERROR

        parts = [f"{client_ip} {method} {path} {status} {duration_ms:.0f}ms"]
        if getattr(settings, "log_request_payload", True) and request_body:
            parts.append(f"  request: {_safe_payload(request_body)}")
        if getattr(settings, "log_response_payload", True) and response_body:
            parts.append(f"  response: {_safe_payload(response_body)}")
        logger.log(log_level, "\n".join(parts))

        return response
