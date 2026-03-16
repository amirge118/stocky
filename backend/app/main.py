import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Register all agents (side-effect: populates AgentRegistry)
from app import agents  # noqa: F401
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.middleware.error_handler import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.request_logging import RequestLoggingMiddleware

# Import models so Alembic can detect them
from app.models.agent_report import AgentReport  # noqa: F401
from app.models.holding import Holding  # noqa: F401
from app.models.stock import Stock  # noqa: F401

# Ensure request logging middleware logs are visible
_logger = logging.getLogger("app.middleware.request_logging")
_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    from app.agents.scheduler import start_scheduler
    await start_scheduler()
    yield
    # Shutdown
    from app.agents.scheduler import stop_scheduler
    await stop_scheduler()
    await engine.dispose()


application = FastAPI(
    title="Stocky API",
    description="Stocky — financial portfolio & stock analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


application.add_middleware(SecurityHeadersMiddleware)
application.add_middleware(RequestLoggingMiddleware)

# CORS middleware
application.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Exception handlers
application.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
application.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
application.add_exception_handler(Exception, general_exception_handler)

# Include routers
application.include_router(api_router, prefix="/api/v1")


@application.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Stocky API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Export for uvicorn: app.main:app
app = application
