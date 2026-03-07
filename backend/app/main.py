from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.middleware.error_handler import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

# Import models so Alembic can detect them
from app.models.agent_report import AgentReport  # noqa: F401
from app.models.holding import Holding  # noqa: F401
from app.models.stock import Stock  # noqa: F401

# Register all agents (side-effect: populates AgentRegistry)
import app.agents  # noqa: F401


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


app = FastAPI(
    title="Stocky API",
    description="Stocky — financial portfolio & stock analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Stocky API",
        "version": "1.0.0",
        "docs": "/docs",
    }
