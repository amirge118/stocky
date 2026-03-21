"""Unit tests for alert service."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, ConditionType
from app.schemas.alert import AlertCreate, AlertUpdate
from app.services import alert_service

# ── Helpers ──────────────────────────────────────────────────────────────────

async def _make_alert(
    db: AsyncSession,
    ticker: str = "AAPL",
    condition_type: ConditionType = ConditionType.ABOVE,
    target_price: Decimal = Decimal("200.00"),
    is_active: bool = True,
) -> Alert:
    data = AlertCreate(ticker=ticker, condition_type=condition_type, target_price=target_price)
    alert = await alert_service.create_alert(db, data)
    if not is_active:
        await alert_service.update_alert(db, alert.id, AlertUpdate(is_active=False))
        await db.refresh(alert)
    return alert


# ── create_alert ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_success(db_session: AsyncSession):
    """create_alert persists and returns a new alert with defaults."""
    data = AlertCreate(ticker="aapl", condition_type=ConditionType.ABOVE, target_price=Decimal("150.00"))
    alert = await alert_service.create_alert(db_session, data)

    assert alert.id is not None
    assert alert.ticker == "AAPL"  # auto-uppercased by schema validator
    assert alert.condition_type == ConditionType.ABOVE
    assert alert.target_price == Decimal("150.00")
    assert alert.is_active is True
    assert alert.last_triggered is None


@pytest.mark.asyncio
async def test_create_alert_below(db_session: AsyncSession):
    data = AlertCreate(ticker="TSLA", condition_type=ConditionType.BELOW, target_price=Decimal("100.50"))
    alert = await alert_service.create_alert(db_session, data)
    assert alert.condition_type == ConditionType.BELOW


@pytest.mark.asyncio
async def test_create_alert_equal(db_session: AsyncSession):
    data = AlertCreate(ticker="MSFT", condition_type=ConditionType.EQUAL, target_price=Decimal("300.00"))
    alert = await alert_service.create_alert(db_session, data)
    assert alert.condition_type == ConditionType.EQUAL


# ── list_alerts ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_alerts_empty(db_session: AsyncSession):
    result = await alert_service.list_alerts(db_session)
    assert result == []


@pytest.mark.asyncio
async def test_list_alerts_returns_all(db_session: AsyncSession):
    await _make_alert(db_session, "AAPL")
    await _make_alert(db_session, "MSFT")
    await _make_alert(db_session, "TSLA")

    result = await alert_service.list_alerts(db_session)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_alerts_respects_limit(db_session: AsyncSession):
    for ticker in ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]:
        await _make_alert(db_session, ticker)

    result = await alert_service.list_alerts(db_session, limit=2)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_alerts_respects_offset(db_session: AsyncSession):
    for ticker in ["AAPL", "MSFT", "TSLA"]:
        await _make_alert(db_session, ticker)

    all_alerts = await alert_service.list_alerts(db_session)
    page2 = await alert_service.list_alerts(db_session, limit=2, offset=2)
    assert len(page2) == 1
    assert page2[0].id == all_alerts[2].id


@pytest.mark.asyncio
async def test_list_alerts_ordered_newest_first(db_session: AsyncSession):
    """list_alerts returns alerts ordered newest-first by created_at (desc)."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import update

    from app.models.alert import Alert

    a1 = await _make_alert(db_session, "AAPL")
    _a2 = await _make_alert(db_session, "MSFT")

    # Force a1 to be 1 hour older so ordering is deterministic
    await db_session.execute(
        update(Alert)
        .where(Alert.id == a1.id)
        .values(created_at=datetime.now(tz=timezone.utc) - timedelta(hours=1))
    )
    await db_session.commit()

    result = await alert_service.list_alerts(db_session)
    tickers = [r.ticker for r in result]
    assert tickers.index("MSFT") < tickers.index("AAPL")


# ── get_alert ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_alert_found(db_session: AsyncSession):
    created = await _make_alert(db_session, "AAPL")
    fetched = await alert_service.get_alert(db_session, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.ticker == "AAPL"


@pytest.mark.asyncio
async def test_get_alert_not_found(db_session: AsyncSession):
    result = await alert_service.get_alert(db_session, 9999)
    assert result is None


# ── update_alert ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_alert_toggle_inactive(db_session: AsyncSession):
    alert = await _make_alert(db_session, "AAPL")
    assert alert.is_active is True

    updated = await alert_service.update_alert(db_session, alert.id, AlertUpdate(is_active=False))
    assert updated is not None
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_update_alert_toggle_active(db_session: AsyncSession):
    alert = await _make_alert(db_session, "AAPL", is_active=False)
    updated = await alert_service.update_alert(db_session, alert.id, AlertUpdate(is_active=True))
    assert updated is not None
    assert updated.is_active is True


@pytest.mark.asyncio
async def test_update_alert_target_price(db_session: AsyncSession):
    alert = await _make_alert(db_session, "AAPL", target_price=Decimal("100.00"))
    updated = await alert_service.update_alert(db_session, alert.id, AlertUpdate(target_price=Decimal("250.00")))
    assert updated is not None
    assert updated.target_price == Decimal("250.00")


@pytest.mark.asyncio
async def test_update_alert_not_found(db_session: AsyncSession):
    result = await alert_service.update_alert(db_session, 9999, AlertUpdate(is_active=False))
    assert result is None


# ── delete_alert ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_alert_success(db_session: AsyncSession):
    alert = await _make_alert(db_session, "AAPL")
    deleted = await alert_service.delete_alert(db_session, alert.id)
    assert deleted is True
    assert await alert_service.get_alert(db_session, alert.id) is None


@pytest.mark.asyncio
async def test_delete_alert_not_found(db_session: AsyncSession):
    result = await alert_service.delete_alert(db_session, 9999)
    assert result is False


# ── get_active_alerts ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_active_alerts_empty(db_session: AsyncSession):
    result = await alert_service.get_active_alerts(db_session)
    assert result == []


@pytest.mark.asyncio
async def test_get_active_alerts_returns_only_active(db_session: AsyncSession):
    active = await _make_alert(db_session, "AAPL", is_active=True)
    await _make_alert(db_session, "MSFT", is_active=False)
    await _make_alert(db_session, "TSLA", is_active=True)

    result = await alert_service.get_active_alerts(db_session)
    ids = [a.id for a in result]
    assert active.id in ids
    assert len(result) == 2
    for a in result:
        assert a.is_active is True


# ── mark_triggered ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_triggered_sets_last_triggered(db_session: AsyncSession):
    from datetime import datetime, timezone

    alert = await _make_alert(db_session, "AAPL")
    assert alert.last_triggered is None

    before = datetime.now(tz=timezone.utc)
    await alert_service.mark_triggered(db_session, alert)
    after = datetime.now(tz=timezone.utc)

    await db_session.refresh(alert)
    assert alert.last_triggered is not None
    assert before <= alert.last_triggered.replace(tzinfo=timezone.utc) <= after


@pytest.mark.asyncio
async def test_mark_triggered_keeps_alert_active(db_session: AsyncSession):
    """Triggering an alert does NOT deactivate it."""
    alert = await _make_alert(db_session, "AAPL")
    await alert_service.mark_triggered(db_session, alert)
    await db_session.refresh(alert)
    assert alert.is_active is True
