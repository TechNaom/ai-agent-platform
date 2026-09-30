"""HNSW cosine indexes on embedding columns (semantic memory / dedup).

Hand-written: autogenerate can't express pgvector operator classes. Names use the
``ix_hnsw_`` prefix so migrations/env.py excludes them from drift comparison.

Revision ID: 0002
Revises: 20723ace4ccf
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "20723ace4ccf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("source_documents", "news_items", "drafts")


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS ix_hnsw_{table}_embedding "
            f"ON {table} USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP INDEX IF EXISTS ix_hnsw_{table}_embedding")
