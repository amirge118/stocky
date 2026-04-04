"""Unit tests for watchlist service."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import watchlist_service


# ── compute_momentum_signals ─────────────────────────────────────────────────

def _make_history(n: int, noise: float = 0.005, spike: float = 0.0) -> dict[date, float]:
    """Generate n daily closes with deterministic noise and an optional spike on the last return.

    Using alternating +noise/-noise ensures sigma > 0 for realistic Z-score tests.
    """
    prices: dict[date, float] = {}
    base = date(2025, 1, 2)
    price = 100.0
    for i in range(n):
        prices[base + timedelta(days=i)] = price
        if i < n - 2:
            # Alternating ±noise so variance is well-defined
            direction = 1.0 if i % 2 == 0 else -1.0
            price *= 1.0 + direction * noise
        else:
            price *= 1.0 + spike
    return prices


@pytest.mark.asyncio
async def test_momentum_signals_empty_symbols():
    """Empty symbol list returns empty signals."""
    result = await watchlist_service.compute_momentum_signals([])
    assert result == []


@pytest.mark.asyncio
async def test_momentum_signals_insufficient_history():
    """Symbol with fewer than 31 closes is excluded from results."""
    short_hist = _make_history(20, spike=0.1)  # only 20 closes
    with patch(
        "app.services.watchlist_service.fetch_history_daily",
        new=AsyncMock(return_value=short_hist),
    ):
        result = await watchlist_service.compute_momentum_signals(["AAPL"])
    assert result == []


@pytest.mark.asyncio
async def test_momentum_signals_z_above_threshold():
    """Symbol with |Z-score| >= 2.0 appears in results with correct direction."""
    hist = _make_history(60, noise=0.005, spike=0.15)  # big spike on last day → high Z
    with patch(
        "app.services.watchlist_service.fetch_history_daily",
        new=AsyncMock(return_value=hist),
    ):
        result = await watchlist_service.compute_momentum_signals(["NVDA"])
    assert len(result) == 1
    assert result[0].symbol == "NVDA"
    assert result[0].direction == "up"
    assert result[0].z_score >= 2.0


@pytest.mark.asyncio
async def test_momentum_signals_z_below_threshold():
    """Symbol with |Z-score| < 2.0 is absent from results."""
    # Last return = +noise (same magnitude as typical returns) → Z ≈ 1, not flagged
    hist = _make_history(60, noise=0.005, spike=0.005)
    with patch(
        "app.services.watchlist_service.fetch_history_daily",
        new=AsyncMock(return_value=hist),
    ):
        result = await watchlist_service.compute_momentum_signals(["MSFT"])
    assert result == []


@pytest.mark.asyncio
async def test_momentum_signals_zero_sigma():
    """Symbol where all returns are identical (sigma=0) is excluded without error."""
    # Flat price — all returns are 0.0, sigma = 0
    hist = {date(2025, 1, 2) + timedelta(days=i): 100.0 for i in range(60)}
    with patch(
        "app.services.watchlist_service.fetch_history_daily",
        new=AsyncMock(return_value=hist),
    ):
        result = await watchlist_service.compute_momentum_signals(["FLAT"])
    assert result == []


@pytest.mark.asyncio
async def test_momentum_signals_down_direction():
    """Large negative move produces direction='down' signal."""
    hist = _make_history(60, noise=0.005, spike=-0.15)
    with patch(
        "app.services.watchlist_service.fetch_history_daily",
        new=AsyncMock(return_value=hist),
    ):
        result = await watchlist_service.compute_momentum_signals(["TSLA"])
    assert len(result) == 1
    assert result[0].direction == "down"
    assert result[0].z_score <= -2.0


@pytest.mark.asyncio
async def test_create_list(db_session: AsyncSession):
    """Creating a list returns the new WatchlistList with correct name."""
    wl = await watchlist_service.create_list(db_session, "Tech Stocks")
    assert wl.id is not None
    assert wl.name == "Tech Stocks"
    assert wl.position == 0


@pytest.mark.asyncio
async def test_get_all_lists_empty(db_session: AsyncSession):
    """get_all_lists returns empty list when no watchlists exist."""
    result = await watchlist_service.get_all_lists(db_session)
    assert result == []


@pytest.mark.asyncio
async def test_get_all_lists_with_item_count(db_session: AsyncSession):
    """get_all_lists returns correct item_count for each list."""
    wl = await watchlist_service.create_list(db_session, "My List")
    await watchlist_service.add_item(db_session, wl.id, "AAPL", "Apple Inc.", "NASDAQ", "Technology")
    await watchlist_service.add_item(db_session, wl.id, "MSFT", "Microsoft", "NASDAQ", "Technology")

    summaries = await watchlist_service.get_all_lists(db_session)
    assert len(summaries) == 1
    assert summaries[0].name == "My List"
    assert summaries[0].item_count == 2


@pytest.mark.asyncio
async def test_get_list_returns_items(db_session: AsyncSession):
    """add_item stores items associated with the correct list."""
    from sqlalchemy import select

    from app.models.watchlist import WatchlistItem

    wl = await watchlist_service.create_list(db_session, "Test")
    await watchlist_service.add_item(db_session, wl.id, "NVDA", "Nvidia", "NASDAQ", None)

    rows = (
        await db_session.execute(
            select(WatchlistItem).where(WatchlistItem.watchlist_id == wl.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].symbol == "NVDA"


@pytest.mark.asyncio
async def test_get_list_not_found(db_session: AsyncSession):
    """get_list returns None for a non-existent id."""
    result = await watchlist_service.get_list(db_session, 9999)
    assert result is None


@pytest.mark.asyncio
async def test_rename_list(db_session: AsyncSession):
    """rename_list updates the name."""
    wl = await watchlist_service.create_list(db_session, "Old Name")
    updated = await watchlist_service.rename_list(db_session, wl.id, "New Name")
    assert updated is not None
    assert updated.name == "New Name"


@pytest.mark.asyncio
async def test_rename_list_not_found(db_session: AsyncSession):
    """rename_list returns None when list does not exist."""
    result = await watchlist_service.rename_list(db_session, 9999, "Whatever")
    assert result is None


@pytest.mark.asyncio
async def test_delete_list(db_session: AsyncSession):
    """delete_list removes the list and returns True."""
    wl = await watchlist_service.create_list(db_session, "To Delete")
    deleted = await watchlist_service.delete_list(db_session, wl.id)
    assert deleted is True
    assert await watchlist_service.get_list(db_session, wl.id) is None


@pytest.mark.asyncio
async def test_delete_list_not_found(db_session: AsyncSession):
    """delete_list returns False when list does not exist."""
    result = await watchlist_service.delete_list(db_session, 9999)
    assert result is False


@pytest.mark.asyncio
async def test_add_item_symbol_uppercased(db_session: AsyncSession):
    """add_item stores the symbol in upper case."""
    wl = await watchlist_service.create_list(db_session, "Casing")
    item = await watchlist_service.add_item(db_session, wl.id, "aapl", "Apple", "NASDAQ", None)
    assert item.symbol == "AAPL"


@pytest.mark.asyncio
async def test_remove_item(db_session: AsyncSession):
    """remove_item deletes the item and returns True."""
    wl = await watchlist_service.create_list(db_session, "Remove Test")
    await watchlist_service.add_item(db_session, wl.id, "TSLA", "Tesla", "NASDAQ", None)

    removed = await watchlist_service.remove_item(db_session, wl.id, "TSLA")
    assert removed is True

    fetched = await watchlist_service.get_list(db_session, wl.id)
    assert fetched is not None
    assert len(fetched.items) == 0


@pytest.mark.asyncio
async def test_remove_item_not_found(db_session: AsyncSession):
    """remove_item returns False when symbol is not in the list."""
    wl = await watchlist_service.create_list(db_session, "Empty")
    result = await watchlist_service.remove_item(db_session, wl.id, "ZZZZZ")
    assert result is False


@pytest.mark.asyncio
async def test_multiple_lists_independent_item_counts(db_session: AsyncSession):
    """Items in separate lists are counted independently."""
    list_a = await watchlist_service.create_list(db_session, "List A")
    list_b = await watchlist_service.create_list(db_session, "List B")

    await watchlist_service.add_item(db_session, list_a.id, "AAPL", "Apple", "NASDAQ", None)
    await watchlist_service.add_item(db_session, list_a.id, "MSFT", "Microsoft", "NASDAQ", None)
    await watchlist_service.add_item(db_session, list_b.id, "TSLA", "Tesla", "NASDAQ", None)

    summaries = await watchlist_service.get_all_lists(db_session)
    counts = {s.name: s.item_count for s in summaries}
    assert counts["List A"] == 2
    assert counts["List B"] == 1
