"""Unit tests for alert Celery task logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.alert import Alert, ConditionType
from app.tasks.alert_tasks import _check_alerts_async, _condition_met


def _execute_result_with_scalar_first(first_value):
    """AsyncMock breaks SQLAlchemy's sync result.scalars().first(); return a plain MagicMock chain."""
    result = MagicMock()
    scalars_rv = MagicMock()
    scalars_rv.first.return_value = first_value
    result.scalars.return_value = scalars_rv
    return result


def _patch_async_session_local(mock_session_cls, *, notification_settings_row=None):
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(
        return_value=_execute_result_with_scalar_first(notification_settings_row)
    )
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_session


# ── _condition_met ────────────────────────────────────────────────────────────

def _alert(condition: ConditionType, target: float) -> Alert:
    a = MagicMock(spec=Alert)
    a.condition_type = condition
    a.target_price = Decimal(str(target))
    return a


def test_condition_above_triggered():
    assert _condition_met(_alert(ConditionType.ABOVE, 100.0), 101.0) is True


def test_condition_above_not_triggered_equal():
    assert _condition_met(_alert(ConditionType.ABOVE, 100.0), 100.0) is False


def test_condition_above_not_triggered_below():
    assert _condition_met(_alert(ConditionType.ABOVE, 100.0), 99.0) is False


def test_condition_below_triggered():
    assert _condition_met(_alert(ConditionType.BELOW, 100.0), 99.0) is True


def test_condition_below_not_triggered_equal():
    assert _condition_met(_alert(ConditionType.BELOW, 100.0), 100.0) is False


def test_condition_below_not_triggered_above():
    assert _condition_met(_alert(ConditionType.BELOW, 100.0), 101.0) is False


def test_condition_equal_exact_match():
    assert _condition_met(_alert(ConditionType.EQUAL, 100.0), 100.0) is True


def test_condition_equal_within_tolerance():
    # 0.001% deviation is within 0.01% tolerance
    assert _condition_met(_alert(ConditionType.EQUAL, 100.0), 100.001) is True


def test_condition_equal_outside_tolerance():
    # 1% deviation exceeds 0.01% tolerance
    assert _condition_met(_alert(ConditionType.EQUAL, 100.0), 101.0) is False


def test_condition_equal_zero_target_zero_price():
    assert _condition_met(_alert(ConditionType.EQUAL, 0.0), 0.0) is True


def test_condition_equal_zero_target_nonzero_price():
    assert _condition_met(_alert(ConditionType.EQUAL, 0.0), 1.0) is False


# ── _check_alerts_async ───────────────────────────────────────────────────────

def _make_db_alert(
    id: int,
    ticker: str,
    condition: ConditionType,
    target: float,
    last_triggered: datetime | None = None,
) -> MagicMock:
    a = MagicMock(spec=Alert)
    a.id = id
    a.ticker = ticker
    a.condition_type = condition
    a.target_price = Decimal(str(target))
    a.last_triggered = last_triggered
    return a


def _make_stock(price: float) -> MagicMock:
    s = MagicMock()
    s.current_price = price
    return s


@pytest.mark.asyncio
async def test_check_alerts_no_active_alerts():
    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = []

        result = await _check_alerts_async()

    assert result == {"checked": 0, "triggered": 0, "failed": 0}


@pytest.mark.asyncio
async def test_check_alerts_triggers_when_condition_met():
    alert = _make_db_alert(1, "AAPL", ConditionType.ABOVE, 100.0, last_triggered=None)

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock) as mock_mark,
        patch("app.tasks.alert_tasks.send_alert_message", new_callable=AsyncMock) as mock_send,
    ):
        mock_session = _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}

        result = await _check_alerts_async()

    assert result["triggered"] == 1
    assert result["failed"] == 0
    mock_mark.assert_awaited_once_with(mock_session, alert)
    mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_alerts_skips_when_condition_not_met():
    alert = _make_db_alert(1, "AAPL", ConditionType.ABOVE, 200.0, last_triggered=None)

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock) as mock_mark,
        patch("app.tasks.alert_tasks.send_alert_message", new_callable=AsyncMock) as mock_send,
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}  # below 200 target

        result = await _check_alerts_async()

    assert result["triggered"] == 0
    mock_mark.assert_not_awaited()
    mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_alerts_skips_within_cooldown():
    recent = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
    alert = _make_db_alert(1, "AAPL", ConditionType.ABOVE, 100.0, last_triggered=recent)

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock) as mock_mark,
        patch("app.tasks.alert_tasks.send_alert_message", new_callable=AsyncMock) as _mock_send,
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}

        result = await _check_alerts_async()

    assert result["triggered"] == 0
    mock_mark.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_alerts_fires_after_cooldown_expires():
    old = datetime.now(tz=timezone.utc) - timedelta(hours=2)
    alert = _make_db_alert(1, "AAPL", ConditionType.ABOVE, 100.0, last_triggered=old)

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock) as mock_mark,
        patch("app.tasks.alert_tasks.send_alert_message", new_callable=AsyncMock) as _mock_send,
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}

        result = await _check_alerts_async()

    assert result["triggered"] == 1
    mock_mark.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_alerts_failed_when_ticker_not_in_price_map():
    alert = _make_db_alert(1, "UNKN", ConditionType.ABOVE, 100.0)

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock) as mock_mark,
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {}  # no prices returned

        result = await _check_alerts_async()

    assert result["failed"] == 1
    assert result["triggered"] == 0
    mock_mark.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_alerts_db_written_before_telegram():
    """mark_triggered must be called before send_alert_message (idempotency)."""
    call_order: list[str] = []
    alert = _make_db_alert(1, "AAPL", ConditionType.ABOVE, 100.0)

    async def fake_mark(db, a):
        call_order.append("mark")

    async def fake_send(**kwargs):
        call_order.append("send")

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", side_effect=fake_mark),
        patch("app.tasks.alert_tasks.send_alert_message", side_effect=fake_send),
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}

        await _check_alerts_async()

    assert call_order == ["mark", "send"]


@pytest.mark.asyncio
async def test_check_alerts_telegram_failure_does_not_raise():
    """A Telegram error must not crash the task."""
    alert = _make_db_alert(1, "AAPL", ConditionType.ABOVE, 100.0)

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock),
        patch("app.tasks.alert_tasks.send_alert_message", side_effect=Exception("Telegram down")),
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = [alert]
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}

        result = await _check_alerts_async()

    # Task should complete; triggered count still incremented
    assert result["triggered"] == 1


@pytest.mark.asyncio
async def test_check_alerts_deduplicates_tickers_for_batch_fetch():
    """Multiple alerts for the same ticker → one fetch call, not N."""
    alerts = [
        _make_db_alert(1, "AAPL", ConditionType.ABOVE, 100.0),
        _make_db_alert(2, "AAPL", ConditionType.BELOW, 300.0),
    ]

    with (
        patch("app.tasks.alert_tasks.AsyncSessionLocal") as mock_session_cls,
        patch("app.tasks.alert_tasks.get_active_alerts", new_callable=AsyncMock) as mock_get,
        patch("app.tasks.alert_tasks.fetch_stock_data_batch", new_callable=AsyncMock) as mock_fetch,
        patch("app.tasks.alert_tasks.mark_triggered", new_callable=AsyncMock),
        patch("app.tasks.alert_tasks.send_alert_message", new_callable=AsyncMock),
    ):
        _patch_async_session_local(mock_session_cls)
        mock_get.return_value = alerts
        mock_fetch.return_value = {"AAPL": _make_stock(150.0)}

        await _check_alerts_async()

    # fetch_stock_data_batch called once with exactly one unique ticker
    mock_fetch.assert_awaited_once()
    tickers_arg = mock_fetch.call_args[0][0]
    assert tickers_arg == ["AAPL"]
