import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.dependencies import get_db_session
from app.core.limiter import limiter
from app.main import app

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session, monkeypatch):
    """Create a test client with rate limiter storage reset to prevent cross-test interference."""
    # Create a sync wrapper for async db_session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_db] = override_get_db

    # Background tasks (e.g. agent trigger) use AsyncSessionLocal from app.core.database.
    # CI uses sqlite :memory: for both test_engine and app engine, but they are different
    # DBs unless we point AsyncSessionLocal at the same session factory as the test.
    monkeypatch.setattr("app.core.database.AsyncSessionLocal", TestSessionLocal)

    # Reset the rate limiter's in-memory storage before each test so request
    # counts from previous tests don't bleed into the current one.
    limiter._limiter.storage.reset()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
