"""Unit tests for app/core/executors.py."""
from concurrent.futures import ThreadPoolExecutor


def test_get_executor_returns_thread_pool_executor():
    from app.core.executors import get_executor

    executor = get_executor()
    assert isinstance(executor, ThreadPoolExecutor)


def test_get_executor_is_idempotent():
    from app.core.executors import get_executor

    executor_a = get_executor()
    executor_b = get_executor()
    assert executor_a is executor_b


def test_get_executor_is_functional():
    from app.core.executors import get_executor

    executor = get_executor()
    future = executor.submit(lambda: 42)
    assert future.result(timeout=5) == 42
