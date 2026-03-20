"""Async httpx client for Financial Modeling Prep (FMP) API."""

import logging
from typing import Any, Optional, Union

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://financialmodelingprep.com"


class FMPRateLimitError(Exception):
    """Raised when FMP returns HTTP 429 Too Many Requests."""


class FMPNotFoundError(Exception):
    """Raised when FMP returns HTTP 404."""


class FMPError(Exception):
    """General FMP API error."""


_retry_on_transient = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


class FMPClient:
    """Thin async wrapper around the FMP REST API."""

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=timeout,
            follow_redirects=True,
        )

    async def get(
        self, path: str, params: Optional[dict[str, Any]] = None
    ) -> Union[list, dict]:
        """GET {path} with automatic API key injection.

        Returns parsed JSON (list or dict).
        Raises FMPRateLimitError on 429, FMPNotFoundError on 404,
        FMPError on other failures.
        """
        full_params = dict(params or {})
        full_params["apikey"] = self._api_key

        try:
            response = await self._client.get(path, params=full_params)
        except httpx.TimeoutException as e:
            raise FMPError(f"FMP request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise FMPError(f"FMP connection error: {e}") from e

        if response.status_code == 429:
            raise FMPRateLimitError("FMP rate limit exceeded (429)")
        if response.status_code == 404:
            raise FMPNotFoundError(f"FMP 404 for {path}")
        if response.status_code == 402:
            logger.debug("FMP 402 (subscription limit) for %s", path)
            return []
        if response.status_code >= 500:
            response.raise_for_status()

        try:
            data = response.json()
        except Exception:
            # Non-JSON response (e.g. "Premium Query Parameter: ..." plain text)
            logger.debug("FMP non-JSON response for %s: %s", path, response.text[:120])
            return []

        # FMP returns {"Error Message": "..."} or {"message": "..."} on errors/limits
        if isinstance(data, dict):
            if "Error Message" in data:
                err = data["Error Message"]
                logger.warning("FMP API error for %s: %s", path, err)
                if "api key" in err.lower() or "invalid" in err.lower():
                    raise FMPError(f"FMP API key error: {err}")
                return []
            if "message" in data and not isinstance(data.get("historical"), list):
                msg = data["message"]
                logger.warning("FMP API message for %s: %s", path, msg)
                if "limit" in msg.lower():
                    raise FMPRateLimitError(f"FMP rate limit: {msg}")
                return []

        return data

    async def aclose(self) -> None:
        await self._client.aclose()


# Module-level singleton; initialized lazily on first use
_fmp_client: Optional["FMPClient"] = None


def get_fmp_client() -> FMPClient:
    """Return the shared FMPClient instance, initializing it on first call."""
    global _fmp_client
    if _fmp_client is None:
        from app.core.config import settings
        _fmp_client = FMPClient(api_key=settings.fmp_api_key)
    return _fmp_client
