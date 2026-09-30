"""Schema behaviour against a real Postgres + pgvector (CI service container)."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_engine.store.models import (
    EMBEDDING_DIM,
    Job,
    JobState,
    Setting,
    Source,
    SourceDocument,
    SourceKind,
)

pytestmark = pytest.mark.db


async def test_source_and_document_roundtrip(session: AsyncSession) -> None:
    src = Source(kind=SourceKind.GITHUB_REPO, name="TechNaom/rag-for-everyone", url="https://x")
    session.add(src)
    await session.flush()
    doc = SourceDocument(
        source_id=src.id,
        path="README.md",
        blob_sha="a" * 40,
        content="# RAG",
        embedding=[0.1] * EMBEDDING_DIM,
    )
    session.add(doc)
    await session.flush()
    stmt = select(SourceDocument).where(SourceDocument.id == doc.id)
    got = (await session.execute(stmt)).scalar_one()
    assert len(got.embedding or []) == EMBEDDING_DIM


async def test_vector_similarity_query(session: AsyncSession) -> None:
    src = Source(kind=SourceKind.GITHUB_REPO, name="repo-sim", url="https://x")
    session.add(src)
    await session.flush()
    near = [1.0] + [0.0] * (EMBEDDING_DIM - 1)
    far = [0.0, 1.0] + [0.0] * (EMBEDDING_DIM - 2)
    session.add_all(
        [
            SourceDocument(
                source_id=src.id, path="near.md", blob_sha="1", content="n", embedding=near
            ),
            SourceDocument(
                source_id=src.id, path="far.md", blob_sha="2", content="f", embedding=far
            ),
        ]
    )
    await session.flush()
    stmt = (
        select(SourceDocument.path)
        .where(SourceDocument.source_id == src.id)
        .order_by(SourceDocument.embedding.cosine_distance(near))
        .limit(1)
    )
    assert (await session.execute(stmt)).scalar_one() == "near.md"


async def test_job_defaults_and_idempotency(session: AsyncSession) -> None:
    session.add(Job(type="scan_repo", payload={"repo": "a"}, idempotency_key="scan:a:1"))
    await session.flush()
    stmt = select(Job).where(Job.idempotency_key == "scan:a:1")
    job = (await session.execute(stmt)).scalar_one()
    assert job.state == JobState.QUEUED and job.attempts == 0 and job.run_after is not None
    session.add(Job(type="scan_repo", idempotency_key="scan:a:1"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_enum_rejects_unknown_value(session: AsyncSession) -> None:
    session.add(Source(kind="not-a-kind", name="bad", url="https://x"))  # type: ignore[arg-type]
    with pytest.raises(StatementError):
        await session.flush()


async def test_settings_jsonb(session: AsyncSession) -> None:
    session.add(Setting(key="mode", value={"mode": "shadow"}))
    await session.flush()
    raw = await session.execute(text("select value->>'mode' from settings where key='mode'"))
    assert raw.scalar_one() == "shadow"
