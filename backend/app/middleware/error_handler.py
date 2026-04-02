import logging

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.schemas.error import ErrorDetail, ErrorResponse

_logger = logging.getLogger(__name__)

# Starlette/FastAPI: prefer UNPROCESSABLE_CONTENT (RFC 9110); keep fallback for older pins.
_HTTP_422_VALIDATION = getattr(
    status,
    "HTTP_422_UNPROCESSABLE_CONTENT",
    status.HTTP_422_UNPROCESSABLE_ENTITY,
)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=_HTTP_422_VALIDATION,
        content=jsonable_encoder(
            ErrorResponse(
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="Request validation failed",
                    details={"errors": exc.errors()},
                )
            )
        ),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=exc.detail,
            )
        ).model_dump(),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """DB errors: return 503 with a useful hint in development."""
    orig = getattr(exc, "orig", None)
    detail = str(orig) if orig is not None else str(exc)
    _logger.exception("Database error: %s", detail)

    if settings.environment == "development":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DATABASE_ERROR",
                    message="Database request failed",
                    details={
                        "detail": detail[:800],
                        "hint": "Check DATABASE_URL, run `alembic upgrade head`, and on macOS "
                        "set DATABASE_SSL_VERIFY=false in backend/.env if you see SSL errors.",
                    },
                )
            ).model_dump(),
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error=ErrorDetail(
                code="DATABASE_ERROR",
                message="Database temporarily unavailable",
            )
        ).model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    import traceback

    print(f"Unhandled exception: {exc}")
    traceback.print_exc()

    # asyncpg + uvloop + TLS in Docker often raises bare OSError(99), not SQLAlchemyError
    if isinstance(exc, OSError) and exc.errno == 99 and settings.environment == "development":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="DATABASE_CONNECT_ERROR",
                    message="Database connection failed (Errno 99)",
                    details={
                        "hint": "If using Docker + Supabase, run uvicorn with "
                        "`--loop asyncio` (see docker-compose.yml). Check DATABASE_URL and SSL settings.",
                    },
                )
            ).model_dump(),
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An internal error occurred",
            )
        ).model_dump(),
    )
