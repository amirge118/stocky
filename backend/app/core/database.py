"""Database connection and session management."""

from __future__ import annotations

import ipaddress
from typing import cast
import logging
import socket
import ssl
from collections.abc import AsyncGenerator
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_logger = logging.getLogger(__name__)

_LOCAL_DB_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "host.docker.internal",
        "::1",
        "postgres",
        "db",
        "database",
    }
)


def _in_docker() -> bool:
    return Path("/.dockerenv").exists()


def _host_is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _resolve_first_ipv4(host: str, port: int) -> str | None:
    """Return first IPv4 for host, or None if resolution fails."""
    if _host_is_ip_literal(host):
        return None
    try:
        infos = socket.getaddrinfo(
            host, port, family=socket.AF_INET, type=socket.SOCK_STREAM
        )
    except OSError as e:
        _logger.warning("IPv4 lookup failed for %s:%s: %s", host, port, e)
        return None
    if not infos:
        return None
    # sockaddr for AF_INET is (host: str, port: int); typeshed still widens [0] to str | int
    return cast(str, infos[0][4][0])


def _should_rewrite_database_url_to_ipv4(url: str) -> bool:
    if not url.startswith("postgresql+asyncpg"):
        return False
    pref = settings.database_prefer_ipv4
    if pref is False:
        return False
    # Supabase pooler hostnames already resolve to IPv4; rewriting to a bare IP breaks TLS/SNI
    # and can surface as InvalidPasswordError even with a correct password.
    try:
        u = make_url(url)
        h = (u.host or "").lower()
        if "pooler.supabase.com" in h:
            return False
    except Exception:
        pass
    if pref is True:
        return True
    # auto: Docker + remote hostname (avoids IPv6 routes that raise Errno 99 with cloud Postgres)
    return _in_docker()


def effective_database_url() -> str:
    """
    DATABASE_URL with hostname rewritten to IPv4 when enabled (Docker auto mode).
    TLS still runs; use DATABASE_SSL_VERIFY=false when connecting by IP if cert checks fail.
    """
    url = settings.database_url
    if not _should_rewrite_database_url_to_ipv4(url):
        return url
    try:
        u = make_url(url)
    except Exception:
        return url
    host = u.host
    if not host or host.lower() in _LOCAL_DB_HOSTS:
        return url
    port = int(u.port or 5432)
    ipv4 = _resolve_first_ipv4(host, port)
    if not ipv4:
        return url
    if ipv4 == host:
        return url
    _logger.info("Using IPv4 %s for database host %s (Docker / DATABASE_PREFER_IPV4)", ipv4, host)
    return str(u.set(host=ipv4))


def _asyncpg_ssl_value() -> bool | ssl.SSLContext:
    """
    Default: verify server certs (ssl=True).

    DATABASE_SSL_VERIFY=false: TLS without verifying the chain (dev only). Use when
    macOS CLI Python / corporate proxy causes SSLCertVerificationError to Supabase,
    or when connecting via IPv4 literal while the cert is issued for the hostname.
    """
    if not settings.database_ssl_verify:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return True


def _asyncpg_connect_args(database_url: str) -> dict:
    """
    asyncpg requires explicit TLS for most cloud Postgres (Supabase, Neon, RDS, etc.).
    Without ssl=True, connections from Docker often fail with OSError errno 99 or SSL errors.

    Local/dev: omit ssl for localhost, 127.0.0.1, host.docker.internal.

    Override: DATABASE_SSL=true|false (force on/off).
    DATABASE_SSL_VERIFY=false disables cert verification (development only).
    """
    if not database_url.startswith("postgresql+asyncpg"):
        return {}
    env = (settings.database_ssl or "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return {}
    if env in ("1", "true", "yes", "on", "require"):
        return {"ssl": _asyncpg_ssl_value()}
    try:
        parsed = urlparse(database_url.replace("postgresql+asyncpg", "http", 1))
    except Exception:
        return {}
    host = (parsed.hostname or "").lower()
    if host in _LOCAL_DB_HOSTS or not host:
        return {}
    return {"ssl": _asyncpg_ssl_value()}


_RESOLVED_DATABASE_URL = effective_database_url()


def warn_if_supabase_ipv6_only_in_docker() -> None:
    """
    Log a clear error when direct db.*.supabase.co is IPv6-only inside Docker (common Errno 99).
    Does not raise — allows health endpoint to surface the failure.
    """
    if not _in_docker():
        return
    raw = (settings.database_url or "").strip()
    if not raw.startswith("postgresql+asyncpg"):
        return
    try:
        u = make_url(raw)
    except Exception:
        return
    host = (u.host or "").lower()
    if not (host.startswith("db.") and host.endswith(".supabase.co")):
        return
    port = int(u.port or 5432)
    if _resolve_first_ipv4(host, port) is not None:
        return
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        return
    has_v4 = any(a[0] == socket.AF_INET for a in infos)
    has_v6 = any(a[0] == socket.AF_INET6 for a in infos)
    if has_v6 and not has_v4:
        _logger.error(
            "DATABASE_URL host %r is IPv6-only. Docker often cannot connect (OSError 99). "
            "Use the Session or Transaction pooler URI from Supabase (host like "
            "aws-0-REGION.pooler.supabase.com). See docs/setup/SUPABASE_DOCKER.md",
            host,
        )


# Create async engine
engine = create_async_engine(
    _RESOLVED_DATABASE_URL,
    echo=settings.environment == "development",
    future=True,
    connect_args=_asyncpg_connect_args(_RESOLVED_DATABASE_URL),
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alembic imports this module before uvicorn lifespan runs — log pooler hint early too.
warn_if_supabase_ipv6_only_in_docker()


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
