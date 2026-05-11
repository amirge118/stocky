"""Unit tests for holding service."""
from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.transaction import Transaction
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


# ── Transaction tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upsert_holding_creates_buy_transaction(db_session: AsyncSession):
    """upsert_holding should create a BUY transaction alongside the holding."""
    await holding_service.upsert_holding(
        db_session, "AAPL", "Apple Inc.", 10.0, 150.0, purchase_date=date(2024, 1, 15)
    )

    result = await db_session.execute(select(Transaction).where(Transaction.symbol == "AAPL"))
    txs = result.scalars().all()
    assert len(txs) == 1
    tx = txs[0]
    assert tx.type == "BUY"
    assert tx.shares == 10.0
    assert tx.price_per_share == 150.0
    assert tx.total_amount == 1500.0
    assert tx.realized_gain is None
    assert tx.transaction_date == date(2024, 1, 15)


@pytest.mark.asyncio
async def test_sell_holding_partial(db_session: AsyncSession):
    """Partial sell: reduces shares, keeps avg_cost, creates SELL transaction."""
    await holding_service.upsert_holding(db_session, "AAPL", "Apple Inc.", 10.0, 150.0)

    result = await holding_service.sell_holding(db_session, "AAPL", 3.0, 180.0)

    assert result is not None
    assert result.shares == pytest.approx(7.0)
    assert result.avg_cost == pytest.approx(150.0)  # unchanged with weighted average
    assert result.total_cost == pytest.approx(1050.0)

    txs_result = await db_session.execute(
        select(Transaction).where(Transaction.symbol == "AAPL", Transaction.type == "SELL")
    )
    sell_txs = txs_result.scalars().all()
    assert len(sell_txs) == 1
    tx = sell_txs[0]
    assert tx.shares == 3.0
    assert tx.price_per_share == 180.0
    assert tx.realized_gain == pytest.approx(90.0)  # (180 - 150) * 3


@pytest.mark.asyncio
async def test_sell_holding_full(db_session: AsyncSession):
    """Full sell: deletes holding, returns None, creates SELL transaction."""
    await holding_service.upsert_holding(db_session, "MSFT", "Microsoft", 5.0, 300.0)

    result = await holding_service.sell_holding(db_session, "MSFT", 5.0, 320.0)

    assert result is None

    holding_result = await db_session.execute(
        select(Holding).where(Holding.symbol == "MSFT")
    )
    assert holding_result.scalar_one_or_none() is None

    tx_result = await db_session.execute(
        select(Transaction).where(Transaction.symbol == "MSFT", Transaction.type == "SELL")
    )
    sell_tx = tx_result.scalar_one()
    assert sell_tx.realized_gain == pytest.approx(100.0)  # (320 - 300) * 5


@pytest.mark.asyncio
async def test_sell_holding_not_found(db_session: AsyncSession):
    """Selling a non-existent holding raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        await holding_service.sell_holding(db_session, "FAKE", 1.0, 100.0)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_sell_holding_over_sell(db_session: AsyncSession):
    """Selling more shares than held raises 422."""
    await holding_service.upsert_holding(db_session, "GOOG", "Alphabet", 2.0, 100.0)

    with pytest.raises(HTTPException) as exc_info:
        await holding_service.sell_holding(db_session, "GOOG", 5.0, 110.0)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_get_transactions_all(db_session: AsyncSession):
    """get_transactions returns all transactions when no symbol filter."""
    await holding_service.upsert_holding(db_session, "AAPL", "Apple", 10.0, 150.0)
    await holding_service.upsert_holding(db_session, "MSFT", "Microsoft", 5.0, 300.0)

    txs = await holding_service.get_transactions(db_session)
    assert len(txs) == 2
    symbols = {t.symbol for t in txs}
    assert symbols == {"AAPL", "MSFT"}


@pytest.mark.asyncio
async def test_get_transactions_filtered(db_session: AsyncSession):
    """get_transactions filters by symbol."""
    await holding_service.upsert_holding(db_session, "AAPL", "Apple", 10.0, 150.0)
    await holding_service.upsert_holding(db_session, "MSFT", "Microsoft", 5.0, 300.0)

    txs = await holding_service.get_transactions(db_session, symbol="AAPL")
    assert len(txs) == 1
    assert txs[0].symbol == "AAPL"
