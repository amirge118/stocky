from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter()

@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="v1",
    )
