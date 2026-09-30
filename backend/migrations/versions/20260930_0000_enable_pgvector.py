"""Enable the pgvector extension (must precede any vector columns).

Revision ID: 0000
Revises:
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0000"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
