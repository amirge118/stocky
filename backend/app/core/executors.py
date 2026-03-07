"""Shared thread pool executor for all sync yfinance operations."""
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=16)


def get_executor() -> ThreadPoolExecutor:
    return _executor
