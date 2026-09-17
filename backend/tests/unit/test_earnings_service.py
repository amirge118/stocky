"""Unit tests for the earnings service."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.earnings_service import (
    get_earnings_for_symbol,
    get_earnings_for_symbols,
)


def _make_earnings_df(rows: list[dict]) -> pd.DataFrame:
    """Build a DataFrame mimicking yfinance Ticker.earnings_dates."""
    if not rows:
        return pd.DataFrame()
    index = pd.DatetimeIndex([r.pop("date") for r in rows])
    return pd.DataFrame(rows, index=index)


@pytest.fixture
def _no_cache(monkeypatch):
    """Disable caching for tests."""
    monkeypatch.setattr("app.services.earnings_service.cache_get", _always_none)
    monkeypatch.setattr("app.services.earnings_service.cache_set", _noop)


async def _always_none(*_a, **_kw):
    return None


async def _noop(*_a, **_kw):
    pass


@pytest.mark.asyncio
async def test_get_earnings_returns_events(_no_cache):
    today = date.today()
    future = today + timedelta(days=30)
    past = today - timedelta(days=90)

    df = _make_earnings_df(
        [
            {
                "date": str(future),
                "EPS Estimate": 1.5,
                "Reported EPS": None,
                "Surprise(%)": None,
            },
            {
                "date": str(past),
                "EPS Estimate": 1.2,
                "Reported EPS": 1.35,
                "Surprise(%)": 12.5,
            },
        ]
    )

    mock_ticker = MagicMock()
    mock_ticker.earnings_dates = df
    mock_ticker.quarterly_financials = pd.DataFrame()

    with patch("app.services.earnings_service.yf.Ticker", return_value=mock_ticker):
        events = await get_earnings_for_symbol("AAPL")

    assert len(events) == 2
    upcoming = [e for e in events if e.is_upcoming]
    assert len(upcoming) == 1
    assert upcoming[0].eps_estimate == 1.5
    assert upcoming[0].days_until is not None

    historical = [e for e in events if not e.is_upcoming]
    assert len(historical) == 1
    assert historical[0].eps_actual == 1.35
    assert historical[0].surprise_pct == 12.5


@pytest.mark.asyncio
async def test_get_earnings_empty_df(_no_cache):
    mock_ticker = MagicMock()
    mock_ticker.earnings_dates = pd.DataFrame()
    mock_ticker.quarterly_financials = pd.DataFrame()

    with patch("app.services.earnings_service.yf.Ticker", return_value=mock_ticker):
        events = await get_earnings_for_symbol("FAKE")

    assert events == []


@pytest.mark.asyncio
async def test_get_earnings_exception_returns_empty(_no_cache):
    with patch(
        "app.services.earnings_service.yf.Ticker", side_effect=Exception("boom")
    ):
        events = await get_earnings_for_symbol("FAIL")

    assert events == []


@pytest.mark.asyncio
async def test_get_earnings_for_symbols_merges(_no_cache):
    today = date.today()
    f1 = today + timedelta(days=10)
    f2 = today + timedelta(days=5)

    def _make_ticker(sym):
        mock = MagicMock()
        d = f1 if sym == "AAPL" else f2
        mock.earnings_dates = _make_earnings_df(
            [
                {
                    "date": str(d),
                    "EPS Estimate": 1.0,
                    "Reported EPS": None,
                    "Surprise(%)": None,
                },
            ]
        )
        mock.quarterly_financials = pd.DataFrame()
        return mock

    with patch("app.services.earnings_service.yf.Ticker", side_effect=_make_ticker):
        events = await get_earnings_for_symbols(["AAPL", "MSFT"])

    # Only upcoming events, sorted by date ascending
    assert len(events) == 2
    assert events[0].earnings_date <= events[1].earnings_date


@pytest.mark.asyncio
async def test_get_earnings_nan_handled(_no_cache):
    """NaN values from yfinance should be returned as None."""
    df = _make_earnings_df(
        [
            {
                "date": str(date.today() - timedelta(days=30)),
                "EPS Estimate": float("nan"),
                "Reported EPS": float("nan"),
                "Surprise(%)": float("nan"),
            },
        ]
    )
    mock_ticker = MagicMock()
    mock_ticker.earnings_dates = df
    mock_ticker.quarterly_financials = pd.DataFrame()

    with patch("app.services.earnings_service.yf.Ticker", return_value=mock_ticker):
        events = await get_earnings_for_symbol("TEST")

    assert len(events) == 1
    assert events[0].eps_estimate is None
    assert events[0].eps_actual is None
    assert events[0].surprise_pct is None
