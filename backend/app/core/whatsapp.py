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

_GRAPH_API_VERSION = "v19.0"


def _messages_url() -> str:
    return (
        f"https://graph.facebook.com/{_GRAPH_API_VERSION}"
        f"/{settings.whatsapp_phone_number_id}/messages"
    )


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }


async def send_whatsapp_message(
    ticker: str,
    condition_type: ConditionType,
    target_price: Decimal,
    current_price: float,
    phone: str,
) -> None:
    """Send a WhatsApp alert message via the Meta Cloud API."""
    if not settings.whatsapp_token or not settings.whatsapp_phone_number_id:
        logger.debug("WhatsApp not configured; skipping notification for %s", ticker)
        return

    phrase = _CONDITION_PHRASE.get(condition_type, "matched")
    text = (
        f"*Price Alert: {ticker}*\n"
        f"{ticker} {phrase} your target of *${target_price}*\n"
        f"Current price: *${current_price}*"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": phone.lstrip("+"),
        "type": "text",
        "text": {"body": text},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _messages_url(), headers=_headers(), json=payload
            )
            response.raise_for_status()
            logger.info("WhatsApp alert sent for %s to %s", ticker, phone)
    except httpx.HTTPStatusError as exc:
        logger.error("WhatsApp HTTP error for %s: %s", ticker, exc)
    except Exception as exc:
        logger.error("WhatsApp send failed for %s: %s", ticker, exc)


async def send_test_whatsapp_message(phone: str) -> tuple[bool, str]:
    """Send a test WhatsApp message to verify configuration."""
    if not settings.whatsapp_token:
        return False, "WhatsApp token is not configured on the server"
    if not settings.whatsapp_phone_number_id:
        return False, "WhatsApp phone number ID is not configured on the server"

    payload = {
        "messaging_product": "whatsapp",
        "to": phone.lstrip("+"),
        "type": "text",
        "text": {"body": "🔔 Stocky: Test notification — your WhatsApp alerts are connected!"},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _messages_url(), headers=_headers(), json=payload
            )
            response.raise_for_status()
            return True, "Test message sent to WhatsApp"
    except httpx.HTTPStatusError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)
