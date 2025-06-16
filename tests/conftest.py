"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from backend.database import get_session


# Test database URL - use a separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/rag_unito"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine, skipping if DB is not available."""
    try:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)

        # Attempt to connect & create tables. If it fails, skip the DB-heavy tests.
        async with engine.begin() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.run_sync(SQLModel.metadata.create_all)

        yield engine

    except Exception as exc:
        pytest.skip(f"Skipping database-dependent tests – cannot connect to Postgres test instance ({exc}).")

    finally:
        # Dispose engine when we actually created it
        if 'engine' in locals():
            await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_session(db_session):
    """Override the get_session dependency for testing."""
    async def _get_session():
        yield db_session
    
    return _get_session 