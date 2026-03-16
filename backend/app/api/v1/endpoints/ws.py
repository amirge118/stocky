"""WebSocket endpoint for real-time stock price updates."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stock_data import fetch_stock_data_from_yfinance

logger = logging.getLogger(__name__)

router = APIRouter()

# symbol -> set of WebSocket connections
_subscribers: dict[str, set[WebSocket]] = {}
_poll_task: Optional[asyncio.Task] = None
_POLL_INTERVAL = 30  # seconds


async def _broadcast_prices() -> None:
    """Poll yfinance for subscribed symbols and broadcast to clients."""
    while True:
        try:
            await asyncio.sleep(_POLL_INTERVAL)
            symbols = list(_subscribers.keys())
            if not symbols:
                continue

            for symbol in symbols:
                try:
                    data = await fetch_stock_data_from_yfinance(symbol)
                    payload = {
                        "type": "price",
                        "symbol": symbol,
                        "price": data.current_price,
                        "change": data.change,
                        "change_percent": data.change_percent,
                    }
                    msg = json.dumps(payload)
                    dead: list[WebSocket] = []
                    for ws in _subscribers.get(symbol, set()):
                        try:
                            await ws.send_text(msg)
                        except Exception:
                            dead.append(ws)
                    for ws in dead:
                        _subscribers[symbol].discard(ws)
                        if not _subscribers[symbol]:
                            del _subscribers[symbol]
                except Exception as e:
                    logger.debug("WS poll error for %s: %s", symbol, e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("WS broadcast error: %s", e)


def _add_subscription(ws: WebSocket, symbols: list[str]) -> None:
    for sym in symbols[:20]:
        s = str(sym).upper().strip()
        if s:
            _subscribers.setdefault(s, set()).add(ws)


def _remove_connection(ws: WebSocket) -> None:
    for symbol, conns in list(_subscribers.items()):
        conns.discard(ws)
        if not conns:
            del _subscribers[symbol]


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket) -> None:
    """WebSocket for real-time stock price updates. Send {'subscribe': ['AAPL', 'MSFT']}."""
    await websocket.accept()
    global _poll_task

    if _poll_task is None or _poll_task.done():
        _poll_task = asyncio.create_task(_broadcast_prices())

    my_symbols: list[str] = []

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                symbols = data.get("subscribe", [])
                if isinstance(symbols, list):
                    my_symbols = [str(s).upper().strip() for s in symbols[:20] if str(s).strip()]
                    _add_subscription(websocket, my_symbols)

                    for symbol in my_symbols:
                        try:
                            price_data = await fetch_stock_data_from_yfinance(symbol)
                            payload = {
                                "type": "price",
                                "symbol": symbol,
                                "price": price_data.current_price,
                                "change": price_data.change,
                                "change_percent": price_data.change_percent,
                            }
                            await websocket.send_text(json.dumps(payload))
                        except Exception:
                            pass
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        _remove_connection(websocket)
