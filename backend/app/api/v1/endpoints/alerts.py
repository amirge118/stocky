from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services import alert_service

router = APIRouter()


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_alert(
    request: Request,
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Create a new price alert."""
    alert = await alert_service.create_alert(db, data)
    return AlertResponse.model_validate(alert)


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    """List all alerts."""
    alerts = await alert_service.list_alerts(db, limit=limit, offset=offset)
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Get a single alert by ID."""
    alert = await alert_service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Update an alert (toggle active, change target price)."""
    alert = await alert_service.update_alert(db, alert_id, data)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an alert."""
    deleted = await alert_service.delete_alert(db, alert_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
