"""Unit tests for the curated sector universe module."""

from app.core.sector_universe import (
    SECTOR_DISPLAY_ORDER,
    SECTOR_UNIVERSE,
    get_symbols_for_sector,
)


def test_all_sectors_have_at_least_8_symbols() -> None:
    for sector, syms in SECTOR_UNIVERSE.items():
        assert len(syms) >= 8, f"{sector} has only {len(syms)} symbols"


def test_all_symbols_are_uppercase() -> None:
    for sector, syms in SECTOR_UNIVERSE.items():
        for sym in syms:
            assert sym == sym.upper(), f"{sym} in {sector} is not uppercase"


def test_no_duplicates_within_sector() -> None:
    for sector, syms in SECTOR_UNIVERSE.items():
        assert len(syms) == len(set(syms)), f"Duplicate symbols in {sector}"


def test_display_order_matches_universe_keys() -> None:
    assert SECTOR_DISPLAY_ORDER == list(SECTOR_UNIVERSE.keys())


def test_get_symbols_exact_case() -> None:
    result = get_symbols_for_sector("Technology")
    assert "AAPL" in result
    assert "MSFT" in result


def test_get_symbols_case_insensitive() -> None:
    result = get_symbols_for_sector("technology")
    assert len(result) > 0
    assert "AAPL" in result


def test_get_symbols_mixed_case() -> None:
    result = get_symbols_for_sector("CONSUMER DISCRETIONARY")
    assert len(result) > 0


def test_get_symbols_unknown_returns_empty() -> None:
    assert get_symbols_for_sector("FakeSector123") == []


def test_get_symbols_respects_limit() -> None:
    result = get_symbols_for_sector("Technology", limit=3)
    assert len(result) == 3


def test_get_symbols_limit_larger_than_universe_returns_all() -> None:
    result = get_symbols_for_sector("Technology", limit=1000)
    universe_count = len(SECTOR_UNIVERSE["Technology"])
    assert len(result) == universe_count


def test_etfs_sector_present() -> None:
    assert "ETFs" in SECTOR_UNIVERSE
    assert "SPY" in SECTOR_UNIVERSE["ETFs"]
    assert "QQQ" in SECTOR_UNIVERSE["ETFs"]


def test_12_sectors_defined() -> None:
    assert len(SECTOR_UNIVERSE) == 12


def test_sectors_with_spaces_work() -> None:
    result = get_symbols_for_sector("Communication Services")
    assert len(result) > 0

    result2 = get_symbols_for_sector("communication services")
    assert result == result2
