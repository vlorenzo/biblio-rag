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


# ---------------------------------------------------------------------------
# Alembic migration helper
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Apply Alembic migrations up to the latest head.

    This helper wraps Alembic's `upgrade head` command so that the database
    schema is created (including extensions and indexes) in a consistent,
    version-controlled way rather than relying on `SQLModel.metadata.create_all`.
    """

    import asyncio
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    # Resolve path to alembic.ini relative to project root (two levels up).
    alembic_ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"

    def _run_upgrade() -> None:  # runs in executor to avoid blocking event loop
        cfg = Config(str(alembic_ini_path))
        # Ensure we use the same DB URL as the application settings (incl. port)
        from backend.config import settings as _settings
        cfg.set_main_option("sqlalchemy.url", _settings.database_url)
        command.upgrade(cfg, "head")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_upgrade) 