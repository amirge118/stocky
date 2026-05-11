"""Integration tests for portfolio sell and transaction endpoints."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models.holding import Holding
from app.models.transaction import Transaction


def _seed_holding(db_session, symbol="AAPL", name="Apple Inc.", shares=10.0, avg_cost=150.0):
    holding = Holding(
        symbol=symbol,
        name=name,
        shares=shares,
        avg_cost=avg_cost,
        total_cost=shares * avg_cost,
    )
    db_session.add(holding)
    db_session.add(
        Transaction(
            symbol=symbol,
            type="BUY",
            shares=shares,
            price_per_share=avg_cost,
            total_amount=shares * avg_cost,
            realized_gain=None,
            transaction_date=date.today(),
        )
    )
    return holding


@pytest.mark.asyncio
async def test_sell_partial_returns_200(client: TestClient, db_session):
    """POST /portfolio/{symbol}/sell with partial shares returns 200 + updated position."""
    _seed_holding(db_session)
    await db_session.commit()

    response = client.post(
        "/api/v1/portfolio/AAPL/sell",
        json={"shares": 3.0, "price_per_share": 180.0},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["shares"] == pytest.approx(7.0)
    assert data["avg_cost"] == pytest.approx(150.0)
    assert data["total_cost"] == pytest.approx(1050.0)


@pytest.mark.asyncio
async def test_sell_full_returns_204(client: TestClient, db_session):
    """POST /portfolio/{symbol}/sell with all shares returns 204 No Content."""
    _seed_holding(db_session)
    await db_session.commit()

    response = client.post(
        "/api/v1/portfolio/AAPL/sell",
        json={"shares": 10.0, "price_per_share": 200.0},
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_sell_not_found_returns_404(client: TestClient, db_session):
    """POST /portfolio/{symbol}/sell for unknown symbol returns 404."""
    response = client.post(
        "/api/v1/portfolio/FAKE/sell",
        json={"shares": 1.0, "price_per_share": 100.0},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sell_over_sell_returns_422(client: TestClient, db_session):
    """POST /portfolio/{symbol}/sell selling more than held returns 422."""
    _seed_holding(db_session, shares=5.0)
    await db_session.commit()

    response = client.post(
        "/api/v1/portfolio/AAPL/sell",
        json={"shares": 10.0, "price_per_share": 200.0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_transactions_empty(client: TestClient):
    """GET /portfolio/transactions returns empty list when no transactions."""
    response = client.get("/api/v1/portfolio/transactions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_transactions_returns_all(client: TestClient, db_session):
    """GET /portfolio/transactions returns all transactions."""
    _seed_holding(db_session, "AAPL", shares=10.0, avg_cost=150.0)
    _seed_holding(db_session, "MSFT", name="Microsoft", shares=5.0, avg_cost=300.0)
    await db_session.commit()

    response = client.get("/api/v1/portfolio/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    symbols = {tx["symbol"] for tx in data}
    assert symbols == {"AAPL", "MSFT"}


@pytest.mark.asyncio
async def test_get_transactions_filtered_by_symbol(client: TestClient, db_session):
    """GET /portfolio/transactions?symbol=AAPL returns only AAPL transactions."""
    _seed_holding(db_session, "AAPL", shares=10.0, avg_cost=150.0)
    _seed_holding(db_session, "MSFT", name="Microsoft", shares=5.0, avg_cost=300.0)
    await db_session.commit()

    response = client.get("/api/v1/portfolio/transactions?symbol=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["type"] == "BUY"


@pytest.mark.asyncio
async def test_sell_creates_sell_transaction(client: TestClient, db_session):
    """Selling shares creates a SELL transaction visible in GET /transactions."""
    _seed_holding(db_session, "AAPL", shares=10.0, avg_cost=150.0)
    await db_session.commit()

    client.post(
        "/api/v1/portfolio/AAPL/sell",
        json={"shares": 4.0, "price_per_share": 170.0},
    )

    response = client.get("/api/v1/portfolio/transactions?symbol=AAPL")
    data = response.json()
    sell_txs = [tx for tx in data if tx["type"] == "SELL"]
    assert len(sell_txs) == 1
    assert sell_txs[0]["shares"] == pytest.approx(4.0)
    assert sell_txs[0]["realized_gain"] == pytest.approx(80.0)  # (170-150)*4
