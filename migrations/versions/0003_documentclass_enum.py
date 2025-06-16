"""add documentclass enum

Revision ID: 0003_documentclass_enum
Revises: 0002_batchstatus_enum
Create Date: 2025-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0003_documentclass_enum"
down_revision: str = "0002_batchstatus_enum"
branch_labels: str | None = None
depends_on: str | None = None

documentclass_enum = sa.Enum(
    "authored_by_subject",
    "subject_library",
    "about_subject",
    "subject_traces",
    name="documentclass",
)

def upgrade() -> None:
    documentclass_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        "documents",
        "document_class",
        type_=documentclass_enum,
        postgresql_using="document_class::documentclass",
    )

def downgrade() -> None:
    op.alter_column(
        "documents",
        "document_class",
        type_=sa.String(),
        postgresql_using="document_class::text",
    )
    documentclass_enum.drop(op.get_bind(), checkfirst=True) 