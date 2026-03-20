from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

import httpx

from app.core.config import settings
from app.models.alert import ConditionType

logger = logging.getLogger(__name__)

_CONDITION_PHRASE = {
    ConditionType.ABOVE: "rose above",
    ConditionType.BELOW: "fell below",
    ConditionType.EQUAL: "reached",
}


async def send_alert_message(
    ticker: str,
    condition_type: ConditionType,
    target_price: Decimal,
    current_price: float,
    chat_id: str | None = None,
) -> None:
    """Send a Telegram notification for a triggered price alert."""
    effective_chat_id = chat_id or settings.telegram_chat_id
    if not settings.telegram_token or not effective_chat_id:
        logger.debug("Telegram not configured; skipping notification for %s", ticker)
        return

    phrase = _CONDITION_PHRASE.get(condition_type, "matched")
    yahoo_url = f"https://finance.yahoo.com/quote/{ticker}"
    text = (
        f"<b>Price Alert: {ticker}</b>\n"
        f"{ticker} {phrase} your target of <b>${target_price}</b>\n"
        f"Current price: <b>${current_price}</b>\n"
        f'<a href="{yahoo_url}">View on Yahoo Finance</a>'
    )

    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    payload = {
        "chat_id": effective_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    logger.warning(
                        "Telegram rate limited; retrying in %ds (attempt %d/%d)",
                        retry_after, attempt + 1, max_retries,
                    )
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                logger.info("Telegram alert sent for %s", ticker)
                return
        except httpx.HTTPStatusError as exc:
            logger.error("Telegram HTTP error for %s: %s", ticker, exc)
            return
        except Exception as exc:
            logger.error("Telegram send failed for %s: %s", ticker, exc)
            return

    logger.error("Telegram: max retries exceeded for %s", ticker)


async def send_test_message(chat_id: str) -> tuple[bool, str]:
    """Send a test Telegram message to verify configuration."""
    if not settings.telegram_token:
        return False, "Telegram bot token is not configured on the server"

    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🔔 Stocky: Test notification — your alerts are connected!",
        "parse_mode": "HTML",
    }

    max_retries = 3
    for _ in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                return True, "Test message sent to Telegram"
        except httpx.HTTPStatusError as exc:
            return False, str(exc)
        except Exception as exc:
            return False, str(exc)

    return False, "Telegram: max retries exceeded"
