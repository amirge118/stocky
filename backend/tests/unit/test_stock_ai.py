"""Unit tests for app/services/stock_ai.py.

Mocks:
- app.services.stock_ai.cache_get
- app.services.stock_ai.cache_set
- app.services.stock_ai.fetch_stock_data_from_yfinance
- app.services.stock_ai.fetch_stock_info
- app.services.stock_ai.anthropic.Anthropic  (the class itself)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.stock import (
    CompareSummaryResponse,
    StockAIAnalysisResponse,
    StockDataResponse,
    StockInfoResponse,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_stock_data(symbol: str = "AAPL") -> StockDataResponse:
    return StockDataResponse(
        symbol=symbol,
        name="Apple Inc.",
        current_price=175.0,
        previous_close=170.0,
        change=5.0,
        change_percent=2.94,
        volume=50_000_000,
        market_cap=2_800_000_000_000.0,
        currency="USD",
    )


def _make_stock_info(symbol: str = "AAPL") -> StockInfoResponse:
    return StockInfoResponse(
        symbol=symbol,
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=2_800_000_000_000.0,
        pe_ratio=28.5,
        fifty_two_week_high=200.0,
        fifty_two_week_low=140.0,
    )


def _make_anthropic_mock(text: str = "test analysis") -> MagicMock:
    """Return a mock anthropic.Anthropic() class whose messages.create() returns *text*."""
    fake_content = MagicMock()
    fake_content.text = text

    fake_message = MagicMock()
    fake_message.content = [fake_content]

    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.return_value = fake_message

    mock_anthropic_cls = MagicMock(return_value=mock_client_instance)
    return mock_anthropic_cls


# ── generate_ai_analysis ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_ai_analysis_cache_hit():
    """Returns the cached StockAIAnalysisResponse without calling Anthropic."""
    cached = StockAIAnalysisResponse(
        symbol="AAPL", analysis="cached analysis text"
    ).model_dump(mode="json")

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=cached,
        ) as mock_get,
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
        ) as mock_anthropic_cls,
    ):
        from app.services.stock_ai import generate_ai_analysis

        result = await generate_ai_analysis("AAPL")

    assert isinstance(result, StockAIAnalysisResponse)
    assert result.symbol == "AAPL"
    assert result.analysis == "cached analysis text"
    mock_get.assert_awaited_once()
    mock_set.assert_not_awaited()
    mock_anthropic_cls.assert_not_called()


@pytest.mark.asyncio
async def test_generate_ai_analysis_success():
    """Cache miss: calls Anthropic, returns correct response, writes to cache."""
    mock_anthropic_cls = _make_anthropic_mock("test analysis")

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.stock_ai.fetch_stock_data_from_yfinance",
            new_callable=AsyncMock,
            return_value=_make_stock_data(),
        ),
        patch(
            "app.services.stock_ai.fetch_stock_info",
            new_callable=AsyncMock,
            return_value=_make_stock_info(),
        ),
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
            mock_anthropic_cls,
        ),
    ):
        from app.services.stock_ai import generate_ai_analysis

        result = await generate_ai_analysis("aapl")

    assert isinstance(result, StockAIAnalysisResponse)
    assert result.symbol == "AAPL"
    assert result.analysis == "test analysis"
    mock_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_ai_analysis_success_when_data_fetches_raise():
    """Upstream data fetches raising exceptions are swallowed; Anthropic still called."""
    mock_anthropic_cls = _make_anthropic_mock("test analysis")

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.stock_ai.fetch_stock_data_from_yfinance",
            new_callable=AsyncMock,
            side_effect=Exception("data unavailable"),
        ),
        patch(
            "app.services.stock_ai.fetch_stock_info",
            new_callable=AsyncMock,
            side_effect=Exception("info unavailable"),
        ),
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
            mock_anthropic_cls,
        ),
    ):
        from app.services.stock_ai import generate_ai_analysis

        result = await generate_ai_analysis("AAPL")

    assert isinstance(result, StockAIAnalysisResponse)
    assert result.symbol == "AAPL"
    assert result.analysis == "test analysis"


@pytest.mark.asyncio
async def test_generate_ai_analysis_anthropic_exception_raises_http_500():
    """Anthropic client raising → HTTPException with 500 status code."""
    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.side_effect = Exception("API quota exceeded")
    mock_anthropic_cls = MagicMock(return_value=mock_client_instance)

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.stock_ai.fetch_stock_data_from_yfinance",
            new_callable=AsyncMock,
            return_value=_make_stock_data(),
        ),
        patch(
            "app.services.stock_ai.fetch_stock_info",
            new_callable=AsyncMock,
            return_value=_make_stock_info(),
        ),
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
            mock_anthropic_cls,
        ),
    ):
        from app.services.stock_ai import generate_ai_analysis

        with pytest.raises(HTTPException) as exc_info:
            await generate_ai_analysis("AAPL")

    assert exc_info.value.status_code == 500


# ── generate_compare_summary ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_compare_summary_empty_symbols():
    """Empty symbol list → CompareSummaryResponse with 'Invalid symbol list.' message."""
    from app.services.stock_ai import generate_compare_summary

    result = await generate_compare_summary([])

    assert isinstance(result, CompareSummaryResponse)
    assert result.summary == "Invalid symbol list."


@pytest.mark.asyncio
async def test_generate_compare_summary_too_many_symbols():
    """More than 5 symbols → CompareSummaryResponse with 'Invalid symbol list.' message."""
    from app.services.stock_ai import generate_compare_summary

    result = await generate_compare_summary(
        ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "NVDA"]
    )

    assert isinstance(result, CompareSummaryResponse)
    assert result.summary == "Invalid symbol list."


@pytest.mark.asyncio
async def test_generate_compare_summary_cache_hit():
    """Returns the cached CompareSummaryResponse without calling Anthropic."""
    syms = ["AAPL", "MSFT"]
    cached = CompareSummaryResponse(
        symbols=syms, summary="cached comparison"
    ).model_dump(mode="json")

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=cached,
        ) as mock_get,
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
        ) as mock_anthropic_cls,
    ):
        from app.services.stock_ai import generate_compare_summary

        result = await generate_compare_summary(syms)

    assert isinstance(result, CompareSummaryResponse)
    assert result.summary == "cached comparison"
    mock_get.assert_awaited_once()
    mock_set.assert_not_awaited()
    mock_anthropic_cls.assert_not_called()


@pytest.mark.asyncio
async def test_generate_compare_summary_success():
    """Cache miss: mocks Anthropic and data fetch; returns CompareSummaryResponse."""
    mock_anthropic_cls = _make_anthropic_mock("stocks comparison summary")

    syms = ["AAPL", "MSFT"]

    async def fake_stock_data(symbol: str) -> StockDataResponse:
        return _make_stock_data(symbol)

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.stock_ai.fetch_stock_data_from_yfinance",
            side_effect=fake_stock_data,
        ),
        patch(
            "app.services.stock_ai.fetch_stock_info",
            new_callable=AsyncMock,
            side_effect=Exception("info unavailable"),
        ),
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
            mock_anthropic_cls,
        ),
    ):
        from app.services.stock_ai import generate_compare_summary

        result = await generate_compare_summary(syms)

    assert isinstance(result, CompareSummaryResponse)
    assert result.summary == "stocks comparison summary"
    assert set(result.symbols) == {"AAPL", "MSFT"}
    mock_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_compare_summary_anthropic_exception_returns_error_response():
    """Anthropic raising → returns CompareSummaryResponse with error message (no HTTPException)."""
    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.side_effect = Exception("rate limit")
    mock_anthropic_cls = MagicMock(return_value=mock_client_instance)

    syms = ["AAPL", "GOOG"]

    async def fake_stock_data(symbol: str) -> StockDataResponse:
        return _make_stock_data(symbol)

    with (
        patch(
            "app.services.stock_ai.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.stock_ai.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.stock_ai.fetch_stock_data_from_yfinance",
            side_effect=fake_stock_data,
        ),
        patch(
            "app.services.stock_ai.fetch_stock_info",
            new_callable=AsyncMock,
            side_effect=Exception("info unavailable"),
        ),
        patch(
            "app.services.stock_ai.anthropic.Anthropic",
            mock_anthropic_cls,
        ),
    ):
        from app.services.stock_ai import generate_compare_summary

        result = await generate_compare_summary(syms)

    assert isinstance(result, CompareSummaryResponse)
    assert "AI comparison unavailable" in result.summary
    mock_set.assert_not_awaited()
