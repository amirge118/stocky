#!/usr/bin/env python3
"""
Seed Redis with 24-hour cached data for dev symbols.

Usage:
  docker exec stocky-backend-1 python scripts/seed_dev_cache.py
  docker exec stocky-backend-1 python scripts/seed_dev_cache.py AAPL TSLA GOOGL
"""
import asyncio
import os
import sys

sys.path.insert(0, "/app")

import redis.asyncio as aioredis

from app.services.market_service import get_market_overview
from app.services.price_service import get_prices
from app.services.stock_data import (
    fetch_stock_data_from_yfinance,
    fetch_stock_dividends,
    fetch_stock_history,
    fetch_stock_info,
    fetch_stock_news,
)

DEV_TTL = 86400
DEFAULT_SYMBOLS = ["AAPL", "NVDA", "MSFT"]
PERIODS = ["1d", "1w", "1m", "6m", "1y", "2y", "5y"]


async def seed(symbols: list[str]) -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = aioredis.from_url(redis_url, decode_responses=True)

    for sym in symbols:
        sym = sym.upper()
        print(f"\n[{sym}]")

        # --- stock_data:{sym} ---
        await r.delete(f"stock_data:{sym}")
        try:
            await fetch_stock_data_from_yfinance(sym)
            await r.expire(f"stock_data:{sym}", DEV_TTL)
            print(f"  ✓ stock_data:{sym}")
        except Exception as exc:
            print(f"  ✗ stock_data:{sym}  ({exc})")

        # --- stock_history:{sym}:{period} ---
        for period in PERIODS:
            key = f"stock_history:{sym}:{period}"
            await r.delete(key)
            try:
                await fetch_stock_history(sym, period)
                await r.expire(key, DEV_TTL)
                print(f"  ✓ {key}")
            except Exception as exc:
                print(f"  ✗ {key}  ({exc})")

        # --- stock_info:{sym} ---
        await r.delete(f"stock_info:{sym}")
        try:
            await fetch_stock_info(sym)
            await r.expire(f"stock_info:{sym}", DEV_TTL)
            print(f"  ✓ stock_info:{sym}")
        except Exception as exc:
            print(f"  ✗ stock_info:{sym}  ({exc})")

        # --- stock_news:{sym}:8 ---
        await r.delete(f"stock_news:{sym}:8")
        try:
            await fetch_stock_news(sym, 8)
            await r.expire(f"stock_news:{sym}:8", DEV_TTL)
            print(f"  ✓ stock_news:{sym}:8")
        except Exception as exc:
            print(f"  ✗ stock_news:{sym}:8  ({exc})")

        # --- stock_dividends:{sym}:5 ---
        await r.delete(f"stock_dividends:{sym}:5")
        try:
            await fetch_stock_dividends(sym, 5)
            await r.expire(f"stock_dividends:{sym}:5", DEV_TTL)
            print(f"  ✓ stock_dividends:{sym}:5")
        except Exception as exc:
            print(f"  ✗ stock_dividends:{sym}:5  ({exc})")

        # --- price:{sym} + price_stale:{sym} ---
        await r.delete(f"price:{sym}")
        await r.delete(f"price_stale:{sym}")
        try:
            await get_prices([sym])
            await r.expire(f"price:{sym}", DEV_TTL)
            # price_stale already has a 24 h TTL from the service; refresh anyway
            await r.expire(f"price_stale:{sym}", DEV_TTL)
            print(f"  ✓ price:{sym}  price_stale:{sym}")
        except Exception as exc:
            print(f"  ✗ price:{sym}  ({exc})")

    # --- market:overview ---
    print("\n[market]")
    await r.delete("market:overview")
    try:
        await get_market_overview()
        await r.expire("market:overview", DEV_TTL)
        print("  ✓ market:overview")
    except Exception as exc:
        print(f"  ✗ market:overview  ({exc})")

    await r.aclose()
    print("\nDone. All keys seeded with 24 h TTL.")


if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_SYMBOLS
    asyncio.run(seed(symbols))
