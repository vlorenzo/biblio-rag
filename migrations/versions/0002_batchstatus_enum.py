"""add batchstatus enum

Revision ID: 0002_batchstatus_enum
Revises: 0001_initial
Create Date: 2025-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0002_batchstatus_enum"
down_revision: str = "0001_initial"
branch_labels: str | None = None
depends_on: str | None = None

batchstatus_enum = sa.Enum(
    "pending",
    "processing",
    "completed",
    "failed",
    name="batchstatus",
)

def upgrade() -> None:
    # Create the enum type in Postgres
    batchstatus_enum.create(op.get_bind(), checkfirst=True)

    # Alter the column type
    op.alter_column(
        "batches",
        "status",
        type_=batchstatus_enum,
        postgresql_using="status::batchstatus",
    )


def downgrade() -> None:
    # Revert column to VARCHAR
    op.alter_column(
        "batches",
        "status",
        type_=sa.String(),
        postgresql_using="status::text",
    )

    batchstatus_enum.drop(op.get_bind(), checkfirst=True) 