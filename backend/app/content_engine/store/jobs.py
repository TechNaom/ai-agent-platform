"""Durable job queue on Postgres (ADR-0004).

Jobs are claimed with ``SELECT … FOR UPDATE SKIP LOCKED`` so any number of workers can
run safely. Handlers must be idempotent; a job may run more than once after a crash.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_engine.store.models import Job, JobState

MAX_ERROR_CHARS = 4000


def _now() -> datetime:
    return datetime.now(UTC)


async def enqueue(
    session: AsyncSession,
    job_type: str,
    payload: dict[str, Any] | None = None,
    *,
    run_after: datetime | None = None,
    priority: int = 0,
    max_attempts: int = 5,
    idempotency_key: str | None = None,
) -> int | None:
    """Insert a job. Returns its id, or None if ``idempotency_key`` already exists."""
    stmt = (
        insert(Job)
        .values(
            type=job_type,
            payload=payload or {},
            state=JobState.QUEUED,
            priority=priority,
            attempts=0,
            max_attempts=max_attempts,
            run_after=run_after or _now(),
            idempotency_key=idempotency_key,
        )
        .on_conflict_do_nothing(index_elements=[Job.idempotency_key])
        .returning(Job.id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def claim(
    session: AsyncSession,
    worker_id: str,
    *,
    limit: int,
    exclude_types_prefix: str | None = None,
) -> list[Job]:
    """Atomically claim up to ``limit`` due jobs, highest priority first."""
    query = (
        select(Job)
        .where(Job.state == JobState.QUEUED, Job.run_after <= _now())
        .order_by(Job.priority.desc(), Job.run_after, Job.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    if exclude_types_prefix:
        query = query.where(~Job.type.startswith(exclude_types_prefix))
    jobs = list((await session.execute(query)).scalars())
    now = _now()
    for job in jobs:
        job.state = JobState.RUNNING
        job.attempts += 1
        job.locked_at = now
        job.locked_by = worker_id
    await session.flush()
    return jobs


async def complete(session: AsyncSession, job: Job) -> None:
    job.state = JobState.SUCCEEDED
    job.locked_at = None
    job.last_error = None
    await session.flush()


def backoff(attempts: int, base_seconds: int) -> timedelta:
    """Exponential backoff: base, 2·base, 4·base … capped at 6 hours."""
    return timedelta(seconds=min(base_seconds * 2 ** max(attempts - 1, 0), 6 * 3600))


async def fail(session: AsyncSession, job: Job, error: str, *, backoff_base_seconds: int) -> None:
    """Record a failure: retry later with backoff, or dead-letter after max attempts."""
    job.last_error = error[:MAX_ERROR_CHARS]
    job.locked_at = None
    if job.attempts >= job.max_attempts:
        job.state = JobState.DEAD
    else:
        job.state = JobState.QUEUED
        job.run_after = _now() + backoff(job.attempts, backoff_base_seconds)
    await session.flush()


async def reclaim_stale(session: AsyncSession, *, lease_seconds: int) -> int:
    """Return jobs stuck in RUNNING past their lease (crashed worker) to the queue."""
    cutoff = _now() - timedelta(seconds=lease_seconds)
    result = await session.execute(
        update(Job)
        .where(
            Job.state == JobState.RUNNING,
            or_(Job.locked_at.is_(None), Job.locked_at < cutoff),
        )
        .values(state=JobState.QUEUED, locked_at=None, locked_by=None)
        .returning(Job.id)
    )
    return len(result.all())
