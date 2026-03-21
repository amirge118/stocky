"""Unit tests for get_sector_peers in app/services/stock_service.py."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.stock import SectorPeerResponse, StockCreate, StockDataResponse, StockInfoResponse


@pytest.mark.asyncio
async def test_get_sector_peers_empty_sector(db_session):
    from app.services.stock_service import get_sector_peers

    result = await get_sector_peers(db_session, sector="")
    assert result == []


@pytest.mark.asyncio
async def test_get_sector_peers_whitespace_sector(db_session):
    from app.services.stock_service import get_sector_peers

    result = await get_sector_peers(db_session, sector="   ")
    assert result == []


@pytest.mark.asyncio
async def test_get_sector_peers_no_stocks_in_db(db_session):
    from app.services.stock_service import get_sector_peers

    mock_data = MagicMock(spec=StockDataResponse)
    mock_data.current_price = 100.0
    mock_data.change_percent = 0.5
    mock_info = MagicMock(spec=StockInfoResponse)
    mock_info.sector = "Technology"
    mock_info.industry = "Software"
    mock_info.pe_ratio = 20.0
    mock_info.market_cap = 1e12

    with (
        patch(
            "app.services.stock_service.fetch_stock_data_from_yfinance",
            new=AsyncMock(return_value=mock_data),
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new=AsyncMock(return_value=mock_info),
        ),
    ):
        result = await get_sector_peers(db_session, sector="Technology")

    assert result == []


@pytest.mark.asyncio
async def test_get_sector_peers_with_stocks(db_session):
    from app.services.stock_service import create_stock, get_sector_peers

    await create_stock(db_session, StockCreate(symbol="AAPL", name="Apple", exchange="NASDAQ", sector="Technology"))

    mock_data = MagicMock(spec=StockDataResponse)
    mock_data.current_price = 150.0
    mock_data.change_percent = 1.5
    mock_info = MagicMock(spec=StockInfoResponse)
    mock_info.sector = "Technology"
    mock_info.industry = "Consumer Electronics"
    mock_info.pe_ratio = 25.0
    mock_info.market_cap = 2e12

    with (
        patch(
            "app.services.stock_service.fetch_stock_data_from_yfinance",
            new=AsyncMock(return_value=mock_data),
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new=AsyncMock(return_value=mock_info),
        ),
    ):
        result = await get_sector_peers(db_session, sector="Technology", current_symbol="AAPL")

    assert len(result) == 1
    peer = result[0]
    assert peer.symbol == "AAPL"
    assert peer.is_current is True
    assert peer.current_price == 150.0
    assert peer.day_change_percent == 1.5
    assert peer.sector == "Technology"
    assert peer.industry == "Consumer Electronics"
    assert peer.pe_ratio == 25.0
    assert peer.market_cap == 2e12


@pytest.mark.asyncio
async def test_get_sector_peers_current_symbol_first(db_session):
    """The stock matching current_symbol should be placed first in the result."""
    from app.services.stock_service import create_stock, get_sector_peers

    await create_stock(db_session, StockCreate(symbol="AAPL", name="Apple", exchange="NASDAQ", sector="Technology"))
    await create_stock(db_session, StockCreate(symbol="MSFT", name="Microsoft", exchange="NASDAQ", sector="Technology"))

    mock_data = MagicMock(spec=StockDataResponse)
    mock_data.current_price = 200.0
    mock_data.change_percent = 0.8
    mock_info = MagicMock(spec=StockInfoResponse)
    mock_info.sector = "Technology"
    mock_info.industry = "Software"
    mock_info.pe_ratio = 30.0
    mock_info.market_cap = 3e12

    with (
        patch(
            "app.services.stock_service.fetch_stock_data_from_yfinance",
            new=AsyncMock(return_value=mock_data),
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new=AsyncMock(return_value=mock_info),
        ),
    ):
        result = await get_sector_peers(db_session, sector="Technology", current_symbol="MSFT")

    assert len(result) == 2
    # MSFT (current) should be first
    assert result[0].symbol == "MSFT"
    assert result[0].is_current is True
    assert result[1].symbol == "AAPL"
    assert result[1].is_current is False


@pytest.mark.asyncio
async def test_get_sector_peers_data_fetch_error_returns_none_fields(db_session):
    """When yfinance calls raise exceptions, the peer is still returned with None fields."""
    from app.services.stock_service import create_stock, get_sector_peers

    await create_stock(db_session, StockCreate(symbol="ERR", name="Error Corp", exchange="NYSE", sector="Finance"))

    with (
        patch(
            "app.services.stock_service.fetch_stock_data_from_yfinance",
            new=AsyncMock(side_effect=Exception("yfinance down")),
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new=AsyncMock(side_effect=Exception("info down")),
        ),
    ):
        result = await get_sector_peers(db_session, sector="Finance")

    assert len(result) == 1
    peer = result[0]
    assert peer.symbol == "ERR"
    assert peer.current_price is None
    assert peer.day_change_percent is None
    assert peer.pe_ratio is None
    assert peer.market_cap is None
    # Falls back to stock.sector from DB when info is unavailable
    assert peer.sector == "Finance"
