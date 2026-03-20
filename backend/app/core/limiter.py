"""Rate limiter — per-user when Authorization header present, else per-IP."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _get_user_or_ip(request: Request) -> str:
    """Use Authorization token as rate-limit key when present, else fall back to IP."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and len(auth) > 7:
        # Hash it to avoid storing raw tokens in Redis keys
        import hashlib
        return "user:" + hashlib.sha256(auth[7:].encode()).hexdigest()[:16]
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_or_ip, default_limits=["200/minute"])
