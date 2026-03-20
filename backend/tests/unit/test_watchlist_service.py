"""Unit tests for watchlist service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import watchlist_service


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
