"""Technical indicator calculations (RSI, MACD, SMA, Bollinger)."""
import math
from typing import Optional
from app.schemas.stock import (
    IndicatorPoint, BollingerPoint, MacdPoint, StockIndicatorsResponse, StockHistoryPoint
)

def _sma(closes: list[float], period: int) -> list[Optional[float]]:
    result: list[Optional[float]] = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        result[i] = sum(closes[i - period + 1 : i + 1]) / period
    return result

def _rsi(closes: list[float], period: int = 14) -> list[Optional[float]]:
    result: list[Optional[float]] = [None] * len(closes)
    if len(closes) < period + 1:
        return result
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period, len(closes)):
        if i > period:
            diff = closes[i] - closes[i - 1]
            avg_gain = (avg_gain * (period - 1) + max(diff, 0)) / period
            avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
        rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
        result[i] = round(100 - 100 / (1 + rs), 2)
    return result

def _ema(closes: list[float], period: int) -> list[Optional[float]]:
    result: list[Optional[float]] = [None] * len(closes)
    if len(closes) < period:
        return result
    sma = sum(closes[:period]) / period
    k = 2 / (period + 1)
    result[period - 1] = sma
    prev = sma
    for i in range(period, len(closes)):
        ema = closes[i] * k + prev * (1 - k)
        result[i] = round(ema, 4)
        prev = ema
    return result

def _macd(closes: list[float]) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd_line: list[Optional[float]] = [
        round(a - b, 4) if a is not None and b is not None else None
        for a, b in zip(ema12, ema26)
    ]
    signal_line: list[Optional[float]] = [None] * len(macd_line)
    hist_line: list[Optional[float]] = [None] * len(macd_line)
    first_valid = next((i for i, v in enumerate(macd_line) if v is not None), None)
    if first_valid is not None:
        seg = [v for v in macd_line[first_valid:] if v is not None]
        seg_ema = _ema(seg, 9)
        for j, v in enumerate(seg_ema):
            idx = first_valid + j
            if idx < len(signal_line):
                signal_line[idx] = v
                if v is not None and macd_line[idx] is not None:
                    hist_line[idx] = round(macd_line[idx] - v, 4)  # type: ignore[operator]
    return macd_line, signal_line, hist_line

def _bollinger(closes: list[float], period: int = 20, std_dev: float = 2.0) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    upper_list: list[Optional[float]] = [None] * len(closes)
    middle_list: list[Optional[float]] = [None] * len(closes)
    lower_list: list[Optional[float]] = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1 : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        upper_list[i] = round(mean + std_dev * std, 4)
        middle_list[i] = round(mean, 4)
        lower_list[i] = round(mean - std_dev * std, 4)
    return upper_list, middle_list, lower_list

def compute_indicators(symbol: str, period: str, points: list[StockHistoryPoint]) -> StockIndicatorsResponse:
    if not points:
        return StockIndicatorsResponse(symbol=symbol, period=period, sma20=[], sma50=[], rsi=[], macd=[], bollinger=[])
    timestamps = [p.t for p in points]
    closes = [p.c for p in points]
    sma20_vals = _sma(closes, 20)
    sma50_vals = _sma(closes, 50)
    rsi_vals = _rsi(closes, 14)
    macd_vals, signal_vals, hist_vals = _macd(closes)
    upper_vals, middle_vals, lower_vals = _bollinger(closes, 20)
    return StockIndicatorsResponse(
        symbol=symbol,
        period=period,
        sma20=[IndicatorPoint(t=t, v=v) for t, v in zip(timestamps, sma20_vals)],
        sma50=[IndicatorPoint(t=t, v=v) for t, v in zip(timestamps, sma50_vals)],
        rsi=[IndicatorPoint(t=t, v=v) for t, v in zip(timestamps, rsi_vals)],
        macd=[MacdPoint(t=t, macd=m, signal=s, hist=h) for t, m, s, h in zip(timestamps, macd_vals, signal_vals, hist_vals)],
        bollinger=[BollingerPoint(t=t, upper=u, middle=mid, lower=lo) for t, u, mid, lo in zip(timestamps, upper_vals, middle_vals, lower_vals)],
    )
