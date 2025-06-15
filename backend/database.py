"""Database connection and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from sqlmodel import SQLModel

from backend.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    future=True,
)


async def create_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)

        # Create HNSW index for efficient vector similarity search (if not exists)
        logger_sql = text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE schemaname = ANY(current_schemas(false))
                      AND indexname = 'idx_chunks_embedding_hnsw') THEN
                    EXECUTE 'CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)';
                END IF;
            END $$;
            """
        )
        await conn.execute(logger_sql)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    # expire_on_commit=False keeps objects usable after commit without lazy refresh,
    # preventing greenlet issues when attributes are accessed by loggers or
    # other sync code running outside the original greenlet.
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose() 