"""Unit tests for get_sector_breakdown and get_portfolio_summary in holding_service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.sector_breakdown import SectorBreakdownResponse
from app.schemas.holding import PortfolioPosition, PortfolioSummary
from app.schemas.stock import StockInfoResponse


def _make_portfolio(positions=None, total_value=0.0):
    return PortfolioSummary(
        positions=positions or [],
        total_value=total_value,
        total_cost=total_value,
        total_gain_loss=0.0,
        total_gain_loss_pct=0.0,
        total_day_change=None,
        total_day_change_pct=None,
    )


def _make_position(symbol, current_value=1000.0):
    return PortfolioPosition(
        symbol=symbol,
        name=f"{symbol} Inc",
        shares=10.0,
        avg_cost=100.0,
        total_cost=1000.0,
        current_price=current_value / 10,
        current_value=current_value,
        gain_loss=0.0,
        gain_loss_pct=0.0,
        portfolio_pct=None,
        day_change=None,
        day_change_percent=None,
    )


@pytest.mark.asyncio
async def test_sector_breakdown_empty(db_session):
    from app.services.holding_service import get_sector_breakdown

    mock_portfolio = _make_portfolio(positions=[], total_value=0.0)
    with patch(
        "app.services.holding_service.get_portfolio",
        new=AsyncMock(return_value=mock_portfolio),
    ):
        result = await get_sector_breakdown(db_session)

    assert isinstance(result, SectorBreakdownResponse)
    assert result.sectors == []
    assert result.total_value == 0.0


@pytest.mark.asyncio
async def test_sector_breakdown_with_positions(db_session):
    from app.services.holding_service import get_sector_breakdown

    pos = _make_position("AAPL", current_value=2000.0)
    mock_portfolio = _make_portfolio(positions=[pos], total_value=2000.0)

    mock_info = MagicMock(spec=StockInfoResponse)
    mock_info.sector = "Technology"

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new=AsyncMock(return_value=mock_portfolio),
        ),
        patch(
            "app.services.holding_service.fetch_stock_info",
            new=AsyncMock(return_value=mock_info),
        ),
    ):
        result = await get_sector_breakdown(db_session)

    assert len(result.sectors) == 1
    assert result.sectors[0].sector == "Technology"
    assert result.sectors[0].total_value == 2000.0
    assert result.sectors[0].weight_pct == 100.0
    assert "AAPL" in result.sectors[0].symbols


@pytest.mark.asyncio
async def test_sector_breakdown_with_multiple_sectors(db_session):
    from app.services.holding_service import get_sector_breakdown

    pos_tech = _make_position("AAPL", current_value=3000.0)
    pos_health = _make_position("JNJ", current_value=1000.0)
    mock_portfolio = _make_portfolio(positions=[pos_tech, pos_health], total_value=4000.0)

    tech_info = MagicMock(spec=StockInfoResponse)
    tech_info.sector = "Technology"
    health_info = MagicMock(spec=StockInfoResponse)
    health_info.sector = "Healthcare"

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new=AsyncMock(return_value=mock_portfolio),
        ),
        patch(
            "app.services.holding_service.fetch_stock_info",
            side_effect=AsyncMock(side_effect=[tech_info, health_info]),
        ),
    ):
        result = await get_sector_breakdown(db_session)

    sectors_by_name = {s.sector: s for s in result.sectors}
    assert "Technology" in sectors_by_name
    assert "Healthcare" in sectors_by_name
    assert sectors_by_name["Technology"].weight_pct == 75.0
    assert sectors_by_name["Healthcare"].weight_pct == 25.0
    # Sorted descending by weight
    assert result.sectors[0].sector == "Technology"


@pytest.mark.asyncio
async def test_sector_breakdown_fetch_info_exception_becomes_unknown(db_session):
    from app.services.holding_service import get_sector_breakdown

    pos = _make_position("ERR", current_value=500.0)
    mock_portfolio = _make_portfolio(positions=[pos], total_value=500.0)

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new=AsyncMock(return_value=mock_portfolio),
        ),
        patch(
            "app.services.holding_service.fetch_stock_info",
            new=AsyncMock(side_effect=Exception("network error")),
        ),
    ):
        result = await get_sector_breakdown(db_session)

    assert len(result.sectors) == 1
    assert result.sectors[0].sector == "Unknown"


@pytest.mark.asyncio
async def test_sector_breakdown_uses_provided_portfolio(db_session):
    """When portfolio is passed in, get_portfolio should NOT be called."""
    from app.services.holding_service import get_sector_breakdown

    pos = _make_position("MSFT", current_value=1500.0)
    provided_portfolio = _make_portfolio(positions=[pos], total_value=1500.0)

    mock_info = MagicMock(spec=StockInfoResponse)
    mock_info.sector = "Technology"

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new=AsyncMock(return_value=None),
        ) as mock_get_portfolio,
        patch(
            "app.services.holding_service.fetch_stock_info",
            new=AsyncMock(return_value=mock_info),
        ),
    ):
        result = await get_sector_breakdown(db_session, portfolio=provided_portfolio)

    mock_get_portfolio.assert_not_called()
    assert result.sectors[0].sector == "Technology"


@pytest.mark.asyncio
async def test_get_portfolio_summary_calls_both(db_session):
    from app.services.holding_service import get_portfolio_summary

    mock_portfolio = _make_portfolio(positions=[], total_value=0.0)
    mock_breakdown = SectorBreakdownResponse(sectors=[], total_value=0.0)

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new=AsyncMock(return_value=mock_portfolio),
        ),
        patch(
            "app.services.holding_service.get_sector_breakdown",
            new=AsyncMock(return_value=mock_breakdown),
        ) as mock_breakdown_fn,
    ):
        portfolio_result, breakdown_result = await get_portfolio_summary(db_session)

    assert portfolio_result is mock_portfolio
    assert breakdown_result is mock_breakdown
    # get_sector_breakdown should receive the portfolio to avoid double fetch
    mock_breakdown_fn.assert_called_once_with(db_session, portfolio=mock_portfolio)
