import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.core.telegram import send_alert_message
from app.models.alert import Alert, ConditionType
from app.services.alert_service import get_active_alerts, mark_triggered
from app.services.stock_data import fetch_stock_data_batch

logger = logging.getLogger(__name__)


def _condition_met(alert: Alert, current_price: float) -> bool:
    target = float(alert.target_price)
    if alert.condition_type == ConditionType.ABOVE:
        return current_price > target
    if alert.condition_type == ConditionType.BELOW:
        return current_price < target
    if alert.condition_type == ConditionType.EQUAL:
        # 0.01% relative tolerance
        if target == 0:
            return current_price == 0
        return abs(current_price - target) / abs(target) <= 0.0001
    return False


async def _check_alerts_async() -> dict:
    async with AsyncSessionLocal() as db:
        alerts = await get_active_alerts(db)
        if not alerts:
            logger.info("check_alerts: no active alerts")
            return {"checked": 0, "triggered": 0, "failed": 0}

        unique_tickers = list({a.ticker for a in alerts})
        price_map = await fetch_stock_data_batch(unique_tickers)

        now = datetime.now(tz=timezone.utc)
        cooldown_cutoff = now - timedelta(hours=1)
        triggered = 0
        failed = 0

        for alert in alerts:
            stock = price_map.get(alert.ticker)
            if not stock:
                failed += 1
                continue

            # Skip if triggered within cooldown window
            if alert.last_triggered and alert.last_triggered > cooldown_cutoff:
                continue

            if not _condition_met(alert, stock.current_price):
                continue

            # Write to DB first for idempotency, then send notification
            await mark_triggered(db, alert)
            triggered += 1

            try:
                await send_alert_message(
                    ticker=alert.ticker,
                    condition_type=alert.condition_type,
                    target_price=Decimal(str(alert.target_price)),
                    current_price=stock.current_price,
                )
            except Exception as exc:
                logger.error("Failed to send Telegram alert for %s: %s", alert.ticker, exc)

        logger.info(
            "check_alerts: checked %d, triggered %d, failed %d",
            len(alerts), triggered, failed,
        )
        return {"checked": len(alerts), "triggered": triggered, "failed": failed}


@celery_app.task(name="app.tasks.alert_tasks.check_alerts", bind=True, max_retries=0)  # type: ignore[misc]
def check_alerts(self: object) -> dict:
    """Celery task: check all active alerts and fire notifications."""
    return asyncio.run(_check_alerts_async())
