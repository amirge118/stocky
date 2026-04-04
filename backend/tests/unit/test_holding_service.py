"""Unit tests for holding service."""
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.schemas.stock import (
    StockDataResponse,
    StockNewsItem,
)
from app.services import holding_service


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_data_from_yfinance")
async def test_get_portfolio_includes_day_change(mock_fetch, db_session: AsyncSession):
    """Test that portfolio positions include day_change and day_change_percent."""
    holding = Holding(
        symbol="AAPL",
        name="Apple Inc.",
        shares=10.0,
        avg_cost=150.0,
        total_cost=1500.0,
    )
    db_session.add(holding)
    await db_session.commit()

    mock_fetch.return_value = StockDataResponse(
        symbol="AAPL",
        name="Apple Inc.",
        current_price=155.0,
        previous_close=150.0,
        change=5.0,
        change_percent=3.33,
        volume=1000000,
        market_cap=2500000000000,
        currency="USD",
    )

    result = await holding_service.get_portfolio(db_session)

    assert len(result.positions) == 1
    pos = result.positions[0]
    assert pos.day_change == 50.0  # 10 shares * $5 change
    assert pos.day_change_percent == 3.33
    assert result.total_day_change == 50.0
    assert result.total_day_change_pct == 3.23  # 50/1550 * 100


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_data_from_yfinance")
async def test_get_portfolio_empty_returns_none_day_change(mock_fetch, db_session: AsyncSession):
    """Test empty portfolio returns None for day change fields."""
    result = await holding_service.get_portfolio(db_session)

    assert result.positions == []
    assert result.total_day_change is None
    assert result.total_day_change_pct is None


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_news")
async def test_get_portfolio_news_empty(mock_fetch, db_session: AsyncSession):
    """Test portfolio news when no holdings."""
    result = await holding_service.get_portfolio_news(db_session)

    assert result == []
    mock_fetch.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_news")
async def test_get_portfolio_news_merges_and_dedupes(mock_fetch, db_session: AsyncSession):
    """Test portfolio news merges from multiple holdings and dedupes by title."""
    for sym, name in [("AAPL", "Apple"), ("MSFT", "Microsoft")]:
        db_session.add(
            Holding(symbol=sym, name=name, shares=1.0, avg_cost=100.0, total_cost=100.0)
        )
    await db_session.commit()

    mock_fetch.side_effect = [
        [
            StockNewsItem(title="Same News", publisher="Reuters", link=None, published_at=1000),
            StockNewsItem(title="AAPL News", publisher="Bloomberg", link=None, published_at=2000),
        ],
        [
            StockNewsItem(title="Same News", publisher="Reuters", link=None, published_at=1000),
            StockNewsItem(title="MSFT News", publisher="CNBC", link=None, published_at=3000),
        ],
    ]

    result = await holding_service.get_portfolio_news(db_session, limit=10)

    assert len(result) == 3  # Same News deduped, plus AAPL News, MSFT News
    titles = [r.title for r in result]
    assert "Same News" in titles
    assert "AAPL News" in titles
    assert "MSFT News" in titles
    assert all(hasattr(r, "symbol") for r in result)


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_data_from_yfinance")
async def test_get_portfolio_includes_purchase_date(mock_fetch, db_session: AsyncSession):
    """Portfolio positions include purchase_date from the holding row."""
    from datetime import date as date_cls

    holding = Holding(
        symbol="AAPL",
        name="Apple Inc.",
        shares=10.0,
        avg_cost=150.0,
        total_cost=1500.0,
        purchase_date=date_cls(2023, 6, 1),
    )
    db_session.add(holding)
    await db_session.commit()

    mock_fetch.return_value = StockDataResponse(
        symbol="AAPL",
        name="Apple Inc.",
        current_price=155.0,
        previous_close=150.0,
        change=5.0,
        change_percent=3.33,
        volume=1000000,
        market_cap=2500000000000,
        currency="USD",
    )

    result = await holding_service.get_portfolio(db_session)
    assert result.positions[0].purchase_date == date_cls(2023, 6, 1)
