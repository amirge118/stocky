"""Unit tests for indicators_service — pure numeric functions."""

import pytest

from app.schemas.stock import StockHistoryPoint, StockIndicatorsResponse
from app.services.indicators_service import (
    _bollinger,
    _ema,
    _macd,
    _rsi,
    _sma,
    compute_indicators,
)


def _make_points(closes: list[float]) -> list[StockHistoryPoint]:
    return [
        StockHistoryPoint(t=i * 1000, o=c, h=c, l=c, c=c, v=None)
        for i, c in enumerate(closes)
    ]


# ---------------------------------------------------------------------------
# SMA
# ---------------------------------------------------------------------------

def test_sma_basic():
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _sma(closes, period=3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(2.0)
    assert result[3] == pytest.approx(3.0)
    assert result[4] == pytest.approx(4.0)


def test_sma_period_equals_length():
    closes = [10.0, 20.0, 30.0]
    result = _sma(closes, period=3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(20.0)


def test_sma_period_larger_than_data():
    closes = [1.0, 2.0]
    result = _sma(closes, period=5)
    assert result == [None, None]


def test_sma_returns_correct_length():
    closes = list(range(10))
    result = _sma(closes, period=3)
    assert len(result) == 10


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------

def test_rsi_insufficient_data_all_none():
    closes = [float(i) for i in range(10)]  # < period + 1 = 15
    result = _rsi(closes, period=14)
    assert all(v is None for v in result)


def test_rsi_all_upward_is_100():
    closes = [float(i) for i in range(1, 20)]  # strictly increasing
    result = _rsi(closes, period=14)
    non_none = [v for v in result if v is not None]
    assert len(non_none) > 0
    assert all(v == 100.0 for v in non_none)


def test_rsi_all_downward_is_0():
    closes = [float(19 - i) for i in range(19)]  # strictly decreasing
    result = _rsi(closes, period=14)
    non_none = [v for v in result if v is not None]
    assert len(non_none) > 0
    assert all(v == 0.0 for v in non_none)


def test_rsi_values_in_valid_range():
    closes = [100.0, 102.0, 101.0, 103.0, 100.0, 98.0, 99.0, 101.0,
              102.0, 105.0, 104.0, 103.0, 102.0, 101.0, 103.0, 105.0]
    result = _rsi(closes, period=14)
    non_none = [v for v in result if v is not None]
    assert len(non_none) > 0
    assert all(0.0 <= v <= 100.0 for v in non_none)


def test_rsi_first_values_are_none():
    closes = [float(i) for i in range(20)]
    result = _rsi(closes, period=14)
    assert all(v is None for v in result[:14])
    assert result[14] is not None


# ---------------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------------

def test_ema_insufficient_data_all_none():
    closes = [1.0, 2.0]
    result = _ema(closes, period=3)
    assert all(v is None for v in result)


def test_ema_starts_with_sma():
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _ema(closes, period=3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(2.0)  # SMA of first 3 values


def test_ema_subsequent_values():
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = _ema(closes, period=3)
    k = 2 / (3 + 1)  # 0.5
    expected_3 = 4.0 * k + 2.0 * (1 - k)  # 3.0
    expected_4 = 5.0 * k + expected_3 * (1 - k)  # 4.0
    assert result[3] == pytest.approx(expected_3, abs=1e-4)
    assert result[4] == pytest.approx(expected_4, abs=1e-4)


def test_ema_returns_correct_length():
    closes = list(range(10))
    result = _ema(closes, period=3)
    assert len(result) == 10


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def test_macd_short_data_all_none():
    closes = [100.0] * 20  # EMA26 needs ≥26 points
    macd_line, signal_line, hist_line = _macd(closes)
    assert all(v is None for v in macd_line)
    assert all(v is None for v in signal_line)
    assert all(v is None for v in hist_line)


def test_macd_returns_three_equal_length_series():
    closes = [float(100 + i) for i in range(50)]
    macd_line, signal_line, hist_line = _macd(closes)
    assert len(macd_line) == 50
    assert len(signal_line) == 50
    assert len(hist_line) == 50


def test_macd_hist_equals_macd_minus_signal():
    closes = [float(100 + i) for i in range(60)]
    macd_line, signal_line, hist_line = _macd(closes)
    for m, s, h in zip(macd_line, signal_line, hist_line):
        if m is not None and s is not None and h is not None:
            assert h == pytest.approx(m - s, abs=1e-3)


def test_macd_first_valid_after_ema26():
    closes = [float(100 + i % 5) for i in range(60)]
    macd_line, _, _ = _macd(closes)
    # EMA26 starts at index 25; first MACD value is at index 25
    assert all(v is None for v in macd_line[:25])
    assert macd_line[25] is not None


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def test_bollinger_constant_price_bands_all_equal():
    closes = [100.0] * 25
    upper, middle, lower = _bollinger(closes, period=20)
    for u, m, lo in zip(upper[19:], middle[19:], lower[19:]):
        assert u == pytest.approx(100.0)
        assert m == pytest.approx(100.0)
        assert lo == pytest.approx(100.0)


def test_bollinger_upper_ge_middle_ge_lower():
    closes = [100.0 + (i % 5) for i in range(30)]
    upper, middle, lower = _bollinger(closes, period=20)
    for u, m, lo in zip(upper, middle, lower):
        if u is not None:
            assert u >= m
            assert m >= lo


def test_bollinger_nones_before_period():
    closes = [100.0] * 25
    upper, middle, lower = _bollinger(closes, period=20)
    assert all(v is None for v in upper[:19])
    assert upper[19] is not None


def test_bollinger_std_dev_scales_bands():
    """Wider std_dev → wider bands around same middle."""
    closes = [float(100 + i % 7) for i in range(30)]
    upper1, middle1, lower1 = _bollinger(closes, period=20, std_dev=1.0)
    upper2, middle2, lower2 = _bollinger(closes, period=20, std_dev=2.0)
    for u1, u2, m1, m2, lo1, lo2 in zip(upper1, upper2, middle1, middle2, lower1, lower2):
        if u1 is not None:
            assert u2 >= u1  # wider upper band
            assert lo2 <= lo1  # narrower lower band
            assert m1 == pytest.approx(m2, abs=1e-6)  # same middle


# ---------------------------------------------------------------------------
# compute_indicators (integration)
# ---------------------------------------------------------------------------

def test_compute_indicators_empty_points():
    result = compute_indicators("AAPL", "1m", [])
    assert result.symbol == "AAPL"
    assert result.period == "1m"
    assert result.sma20 == []
    assert result.sma50 == []
    assert result.rsi == []
    assert result.macd == []
    assert result.bollinger == []


def test_compute_indicators_returns_correct_schema():
    closes = [float(100 + i % 10) for i in range(60)]
    points = _make_points(closes)
    result = compute_indicators("MSFT", "6m", points)
    assert isinstance(result, StockIndicatorsResponse)
    assert result.symbol == "MSFT"
    assert result.period == "6m"


def test_compute_indicators_all_series_same_length_as_input():
    closes = [float(100 + i % 10) for i in range(60)]
    points = _make_points(closes)
    result = compute_indicators("AAPL", "1y", points)
    n = len(points)
    assert len(result.sma20) == n
    assert len(result.sma50) == n
    assert len(result.rsi) == n
    assert len(result.macd) == n
    assert len(result.bollinger) == n


def test_compute_indicators_timestamps_match_input():
    closes = [float(i + 100) for i in range(60)]
    points = _make_points(closes)
    result = compute_indicators("AAPL", "1y", points)
    expected_ts = [p.t for p in points]
    assert [p.t for p in result.sma20] == expected_ts
    assert [p.t for p in result.rsi] == expected_ts
    assert [p.t for p in result.bollinger] == expected_ts
