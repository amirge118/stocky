"""Unit tests for app/middleware/error_handler.py.

All four async handlers are called directly — no TestClient required.
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.middleware.error_handler import (
    general_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request() -> Request:
    return MagicMock(spec=Request)


# ---------------------------------------------------------------------------
# validation_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validation_exception_handler_returns_422():
    """Handler returns HTTP 422 with VALIDATION_ERROR code."""
    request = _make_request()
    exc = RequestValidationError(
        errors=[{"loc": ("body", "ticker"), "msg": "field required", "type": "missing"}]
    )

    response = await validation_exception_handler(request, exc)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    body = response.body
    import json
    data = json.loads(body)
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed"
    assert "errors" in data["error"]["details"]


@pytest.mark.asyncio
async def test_validation_exception_handler_embeds_error_list():
    """Validation errors from the exception are included in details."""
    request = _make_request()
    raw_errors = [
        {"loc": ("body", "price"), "msg": "value is not a valid float", "type": "type_error.float"}
    ]
    exc = RequestValidationError(errors=raw_errors)

    response = await validation_exception_handler(request, exc)

    import json
    data = json.loads(response.body)
    assert len(data["error"]["details"]["errors"]) == 1


# ---------------------------------------------------------------------------
# http_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_exception_handler_maps_status_and_detail():
    """Handler echoes the exception's status code and detail message."""
    request = _make_request()
    exc = StarletteHTTPException(status_code=404, detail="Not found")

    response = await http_exception_handler(request, exc)

    import json
    assert response.status_code == 404
    data = json.loads(response.body)
    assert data["error"]["code"] == "HTTP_404"
    assert data["error"]["message"] == "Not found"


@pytest.mark.asyncio
async def test_http_exception_handler_403():
    """Handler works for 403 Forbidden as well."""
    request = _make_request()
    exc = StarletteHTTPException(status_code=403, detail="Forbidden")

    response = await http_exception_handler(request, exc)

    import json
    assert response.status_code == 403
    data = json.loads(response.body)
    assert data["error"]["code"] == "HTTP_403"
    assert data["error"]["message"] == "Forbidden"


# ---------------------------------------------------------------------------
# sqlalchemy_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sqlalchemy_exception_handler_development_returns_detail():
    """In development mode the handler exposes the database error detail."""
    request = _make_request()
    exc = SQLAlchemyError("connection refused")

    with patch("app.middleware.error_handler.settings") as mock_settings:
        mock_settings.environment = "development"
        response = await sqlalchemy_exception_handler(request, exc)

    import json
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = json.loads(response.body)
    assert data["error"]["code"] == "DATABASE_ERROR"
    assert data["error"]["message"] == "Database request failed"
    assert "detail" in data["error"]["details"]
    assert "hint" in data["error"]["details"]


@pytest.mark.asyncio
async def test_sqlalchemy_exception_handler_production_hides_detail():
    """In non-development mode the handler returns only a generic message."""
    request = _make_request()
    exc = SQLAlchemyError("super secret internal connection string here")

    with patch("app.middleware.error_handler.settings") as mock_settings:
        mock_settings.environment = "production"
        response = await sqlalchemy_exception_handler(request, exc)

    import json
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = json.loads(response.body)
    assert data["error"]["code"] == "DATABASE_ERROR"
    assert data["error"]["message"] == "Database temporarily unavailable"
    # details must NOT be present in production
    assert data["error"].get("details") is None


@pytest.mark.asyncio
async def test_sqlalchemy_exception_handler_uses_orig_when_present():
    """Handler prefers exc.orig over str(exc) for the detail message."""
    request = _make_request()
    exc = SQLAlchemyError("outer message")
    exc.orig = Exception("inner cause")  # type: ignore[attr-defined]

    with patch("app.middleware.error_handler.settings") as mock_settings:
        mock_settings.environment = "development"
        response = await sqlalchemy_exception_handler(request, exc)

    import json
    data = json.loads(response.body)
    assert "inner cause" in data["error"]["details"]["detail"]


# ---------------------------------------------------------------------------
# general_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_general_exception_handler_plain_exception_returns_500():
    """A plain Exception produces HTTP 500 with INTERNAL_ERROR code."""
    request = _make_request()
    exc = ValueError("something went wrong")

    response = await general_exception_handler(request, exc)

    import json
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = json.loads(response.body)
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert data["error"]["message"] == "An internal error occurred"


@pytest.mark.asyncio
async def test_general_exception_handler_oserror_errno99_development_returns_503():
    """OSError(errno=99) in development yields 503 with DATABASE_CONNECT_ERROR."""
    request = _make_request()
    exc = OSError(99, "Cannot assign requested address")

    with patch("app.middleware.error_handler.settings") as mock_settings:
        mock_settings.environment = "development"
        response = await general_exception_handler(request, exc)

    import json
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = json.loads(response.body)
    assert data["error"]["code"] == "DATABASE_CONNECT_ERROR"
    assert "hint" in data["error"]["details"]


@pytest.mark.asyncio
async def test_general_exception_handler_oserror_errno99_production_returns_500():
    """OSError(errno=99) in production falls through to the generic 500 path."""
    request = _make_request()
    exc = OSError(99, "Cannot assign requested address")

    with patch("app.middleware.error_handler.settings") as mock_settings:
        mock_settings.environment = "production"
        response = await general_exception_handler(request, exc)

    import json
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = json.loads(response.body)
    assert data["error"]["code"] == "INTERNAL_ERROR"


@pytest.mark.asyncio
async def test_general_exception_handler_oserror_other_errno_returns_500():
    """OSError with a different errno always falls through to the generic 500."""
    request = _make_request()
    exc = OSError(111, "Connection refused")  # errno 111, not 99

    with patch("app.middleware.error_handler.settings") as mock_settings:
        mock_settings.environment = "development"
        response = await general_exception_handler(request, exc)

    import json
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = json.loads(response.body)
    assert data["error"]["code"] == "INTERNAL_ERROR"
