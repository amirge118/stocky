from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    health,
    market,
    portfolio,
    stocks,
    watchlists,
    ws,
)
from app.api.v1.endpoints import settings as notification_settings

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(ws.router, tags=["websocket"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(notification_settings.router, prefix="/settings", tags=["settings"])
