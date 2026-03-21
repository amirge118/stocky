"""Unit tests for add_holding (upsert) and delete_holding in holding_service.py."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.holding import HoldingResponse
from app.services.holding_service import delete_holding, upsert_holding


# ── upsert_holding (add_holding) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_holding_creates_new(db_session: AsyncSession):
    """upsert_holding inserts a brand-new holding and returns correct HoldingResponse."""
    result = await upsert_holding(
        db_session,
        symbol="AAPL",
        name="Apple Inc.",
        shares=10,
        price_per_share=150.0,
    )

    assert isinstance(result, HoldingResponse)
    assert result.symbol == "AAPL"
    assert result.shares == 10.0
    assert result.avg_cost == 150.0
    assert result.total_cost == 1500.0


@pytest.mark.asyncio
async def test_upsert_holding_updates_existing_weighted_avg(db_session: AsyncSession):
    """upsert_holding on an existing symbol computes weighted average cost."""
    # First purchase: 10 shares at $150 → avg_cost = 150, total = 1500
    await upsert_holding(
        db_session,
        symbol="AAPL",
        name="Apple Inc.",
        shares=10,
        price_per_share=150.0,
    )

    # Second purchase: 10 shares at $160 → weighted avg = (1500 + 1600) / 20 = 155
    result = await upsert_holding(
        db_session,
        symbol="AAPL",
        name="Apple Inc.",
        shares=10,
        price_per_share=160.0,
    )

    assert isinstance(result, HoldingResponse)
    assert result.shares == 20.0
    assert result.avg_cost == 155.0
    assert result.total_cost == 3100.0


# ── delete_holding ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_holding_removes_existing(db_session: AsyncSession):
    """delete_holding returns True and removes a holding that exists."""
    await upsert_holding(
        db_session,
        symbol="AAPL",
        name="Apple Inc.",
        shares=5,
        price_per_share=100.0,
    )

    deleted = await delete_holding(db_session, "AAPL")

    assert deleted is True


@pytest.mark.asyncio
async def test_delete_holding_not_found_returns_false(db_session: AsyncSession):
    """delete_holding returns False when the symbol does not exist."""
    result = await delete_holding(db_session, "NONEXISTENT")

    assert result is False
