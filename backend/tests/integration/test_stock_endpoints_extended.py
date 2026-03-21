"""Integration tests for stock API endpoints — extended coverage."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.stock import (
    CompareSummaryResponse,
    SectorPeerResponse,
    StockAIAnalysisResponse,
    StockDataResponse,
    StockDividendsResponse,
    StockEnrichedData,
    StockHistoryResponse,
    StockIndicatorsResponse,
    StockInfoResponse,
    StockNewsItem,
    StockSearchResult,
)

# ── OPTIONS preflight ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_options_stocks(client: TestClient):
    r = client.options("/api/v1/stocks")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_options_batch_data(client: TestClient):
    r = client.options("/api/v1/stocks/batch-data")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_options_enriched_batch(client: TestClient):
    r = client.options("/api/v1/stocks/enriched-batch")
    assert r.status_code == 200


# ── POST /batch-data ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_stock_data_success(client: TestClient):
    mock_result = {
        "AAPL": StockDataResponse(
            symbol="AAPL",
            name="Apple Inc.",
            current_price=175.0,
            previous_close=170.0,
            change=5.0,
            change_percent=2.94,
            volume=50000000,
            market_cap=2_700_000_000_000.0,
            currency="USD",
        ),
        "TSLA": StockDataResponse(
            symbol="TSLA",
            name="Tesla Inc.",
            current_price=250.0,
            previous_close=240.0,
            change=10.0,
            change_percent=4.17,
            volume=30000000,
            market_cap=800_000_000_000.0,
            currency="USD",
        ),
    }
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_data_batch",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.post("/api/v1/stocks/batch-data", json={"symbols": ["AAPL", "TSLA"]})

    assert r.status_code == 200
    data = r.json()
    assert "AAPL" in data
    assert "TSLA" in data
    assert data["AAPL"]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_batch_stock_data_empty_symbols_rejected(client: TestClient):
    """Empty symbols list should be rejected by Pydantic (min_length=1)."""
    r = client.post("/api/v1/stocks/batch-data", json={"symbols": []})
    assert r.status_code == 422


# ── POST /enriched-batch ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_enriched_batch_success(client: TestClient):
    mock_result = {
        "AAPL": StockEnrichedData(
            symbol="AAPL",
            fifty_two_week_high=199.0,
            fifty_two_week_low=124.0,
            avg_volume=60_000_000,
            analyst_rating="buy",
        )
    }
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_enriched_batch",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.post("/api/v1/stocks/enriched-batch", json={"symbols": ["AAPL"]})

    assert r.status_code == 200
    data = r.json()
    assert "AAPL" in data
    assert data["AAPL"]["analyst_rating"] == "buy"


# ── GET /compare-summary ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_compare_summary_success(client: TestClient):
    mock_result = CompareSummaryResponse(
        symbols=["AAPL", "TSLA"],
        summary="AAPL is a more stable investment than TSLA.",
    )
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.generate_compare_summary",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/compare-summary?symbols=AAPL,TSLA")

    assert r.status_code == 200
    data = r.json()
    assert "AAPL" in data["symbols"]
    assert "TSLA" in data["symbols"]
    assert "summary" in data


# ── GET /sector-peers ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sector_peers_success(client: TestClient):
    mock_result = [
        SectorPeerResponse(
            symbol="MSFT",
            name="Microsoft Corp.",
            sector="Technology",
            industry="Software",
            current_price=420.0,
            day_change_percent=0.5,
            pe_ratio=35.0,
            market_cap=3_100_000_000_000.0,
            is_current=False,
        ),
        SectorPeerResponse(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            current_price=175.0,
            day_change_percent=1.2,
            pe_ratio=30.0,
            market_cap=2_700_000_000_000.0,
            is_current=True,
        ),
    ]
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.get_sector_peers",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/sector-peers?sector=Technology")

    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert any(p["symbol"] == "AAPL" for p in data)


# ── GET /search ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_stocks_via_yfinance(client: TestClient):
    mock_result = [
        StockSearchResult(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            current_price=175.0,
            currency="USD",
            country="United States",
            sparkline=[170.0, 172.0, 175.0],
        )
    ]
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.search_stocks_from_yfinance",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/search?q=apple")

    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_search_stocks_non_ascii_returns_empty(client: TestClient):
    """Non-ASCII query short-circuits before calling the service."""
    r = client.get("/api/v1/stocks/search?q=株式")
    assert r.status_code == 200
    assert r.json() == []


# ── GET /{symbol}/history ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_history_success(client: TestClient):
    mock_result = StockHistoryResponse(symbol="AAPL", period="1m", data=[])
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_history",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/AAPL/history?period=1m")

    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["period"] == "1m"


# ── GET /{symbol}/info ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_info_success(client: TestClient):
    mock_result = StockInfoResponse(
        symbol="AAPL",
        description="Apple designs consumer electronics.",
        website="https://apple.com",
        employees=160000,
        country="United States",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=2_700_000_000_000.0,
        pe_ratio=30.0,
        beta=1.2,
        dividend_yield=0.5,
        fifty_two_week_high=199.0,
        fifty_two_week_low=124.0,
        average_volume=60_000_000,
    )
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_info",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/AAPL/info")

    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["sector"] == "Technology"


# ── GET /{symbol}/news ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_news_success(client: TestClient):
    mock_result = [
        StockNewsItem(
            title="Apple reports record quarterly revenue",
            publisher="Reuters",
            link="https://reuters.com/apple-revenue",
            published_at=1_700_000_000_000,
        ),
        StockNewsItem(
            title="Apple launches new iPhone",
            publisher="Bloomberg",
            link="https://bloomberg.com/apple-iphone",
            published_at=1_699_000_000_000,
        ),
    ]
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_news",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/AAPL/news")

    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["title"] == "Apple reports record quarterly revenue"


# ── GET /{symbol}/analysis ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_analysis_success(client: TestClient):
    mock_result = StockAIAnalysisResponse(
        symbol="AAPL",
        analysis="Apple remains a strong buy with solid fundamentals.",
    )
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.generate_ai_analysis",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/AAPL/analysis")

    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert "analysis" in data


# ── GET /{symbol}/dividends ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_dividends_success(client: TestClient):
    mock_result = StockDividendsResponse(
        symbol="AAPL",
        currency="USD",
        dividends=[],
        annual_yield=0.55,
    )
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_dividends",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/AAPL/dividends")

    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["currency"] == "USD"


# ── GET /{symbol}/indicators ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_indicators_success(client: TestClient):
    history_mock = StockHistoryResponse(symbol="AAPL", period="6m", data=[])
    indicators_mock = StockIndicatorsResponse(
        symbol="AAPL",
        period="6m",
        sma20=[],
        sma50=[],
        rsi=[],
        macd=[],
        bollinger=[],
    )
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_history",
        new_callable=AsyncMock,
        return_value=history_mock,
    ), patch(
        "app.api.v1.endpoints.stocks.compute_indicators",
        return_value=indicators_mock,
    ):
        r = client.get("/api/v1/stocks/AAPL/indicators?period=6m")

    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["period"] == "6m"
    assert "sma20" in data
    assert "rsi" in data


# ── GET /{symbol}/data ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_data_success(client: TestClient):
    mock_result = StockDataResponse(
        symbol="AAPL",
        name="Apple Inc.",
        current_price=175.0,
        previous_close=170.0,
        change=5.0,
        change_percent=2.94,
        volume=50_000_000,
        market_cap=2_700_000_000_000.0,
        currency="USD",
    )
    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_data_from_yfinance",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/stocks/AAPL/data")

    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["current_price"] == 175.0
