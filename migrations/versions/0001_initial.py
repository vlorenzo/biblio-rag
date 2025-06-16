"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2024-06-16

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:  # noqa: D401 – Alembic signature
    """Apply the initial schema (documents, content_files, batches, chunks)."""

    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Documents -----------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(), nullable=False, index=True),
        sa.Column("author", sa.String(), nullable=True, index=True),
        sa.Column("document_class", sa.String(), nullable=False, index=True),
        sa.Column("publication_year", sa.Integer(), nullable=True, index=True),
        sa.Column("publisher", sa.String(), nullable=True),
        sa.Column("isbn", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("subject_tags", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.String(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    # Batches --------------------------------------------------------------------
    op.create_table(
        "batches",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("status", sa.String(), nullable=False, index=True),
        sa.Column("parameters", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("total_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # Content files --------------------------------------------------------------
    op.create_table(
        "content_files",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("filename", sa.String(), nullable=False, index=True),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(), nullable=False, index=True),
        sa.Column("content_type", sa.String(), nullable=False),
    )

    # Chunks ---------------------------------------------------------------------
    op.create_table(
        "chunks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("batch_id", sa.UUID(), sa.ForeignKey("batches.id"), nullable=False, index=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False, index=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(), nullable=False, index=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
    )

    # HNSW index for vector similarity (if pgvector >=0.5)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE indexname = 'idx_chunks_embedding_hnsw'
            ) THEN
                CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
            END IF;
        END$$;
        """
    )


def downgrade() -> None:  # noqa: D401 – Alembic signature
    """Drop all tables created in upgrade()."""

    op.drop_index("idx_chunks_embedding_hnsw", table_name="chunks", if_exists=True)
    op.drop_table("chunks")
    op.drop_table("content_files")
    op.drop_table("batches")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector") 