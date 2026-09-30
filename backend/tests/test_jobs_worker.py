"""Job queue + worker against a real Postgres (CI service container)."""

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.content_engine.store import jobs as job_store
from app.content_engine.store import settings_repo
from app.content_engine.store.models import Job, JobState, PublishMode
from app.core.config import Settings
from app.worker.breaker import CircuitBreaker
from app.worker.main import Worker
from app.worker.registry import JobContext, Registry

pytestmark = pytest.mark.db


@pytest.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    engine = create_async_engine(url)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE jobs, settings RESTART IDENTITY"))
    await engine.dispose()


def _settings() -> Settings:
    return Settings(worker_batch_size=10, job_backoff_base_seconds=30, job_lease_seconds=60)


async def _state(maker: async_sessionmaker[AsyncSession], job_id: int) -> Job:
    async with maker() as s:
        return (await s.execute(select(Job).where(Job.id == job_id))).scalar_one()


async def test_enqueue_is_idempotent(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions.begin() as s:
        first = await job_store.enqueue(s, "scan.github", {"repo": "a"}, idempotency_key="k1")
        second = await job_store.enqueue(s, "scan.github", {"repo": "a"}, idempotency_key="k1")
    assert first is not None and second is None


async def test_concurrent_claims_are_disjoint(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions.begin() as s:
        for i in range(6):
            await job_store.enqueue(s, "scan.github", {"i": i})

    async def claim(worker: str) -> list[int]:
        async with sessions.begin() as s:
            got = await job_store.claim(s, worker, limit=5)
            await asyncio.sleep(0.2)  # hold locks while the other worker claims
            return [j.id for j in got]

    a, b = await asyncio.gather(claim("w1"), claim("w2"))
    assert set(a).isdisjoint(b)
    assert len(a) + len(b) == 6


async def test_future_jobs_not_claimed(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions.begin() as s:
        later = datetime.now(UTC) + timedelta(hours=1)
        await job_store.enqueue(s, "scan.github", run_after=later)
        assert await job_store.claim(s, "w", limit=5) == []


async def test_failure_backoff_then_dead_letter(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions.begin() as s:
        job_id = await job_store.enqueue(s, "x.y", max_attempts=2)
    assert job_id is not None
    for expected in (JobState.QUEUED, JobState.DEAD):
        async with sessions.begin() as s:
            job = await s.get(Job, job_id, with_for_update=True)
            assert job is not None
            job.attempts += 1
            await job_store.fail(s, job, "boom", backoff_base_seconds=30)
        job = await _state(sessions, job_id)
        assert job.state == expected
    assert job.last_error == "boom"


async def test_reclaim_stale_running_job(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions.begin() as s:
        job_id = await job_store.enqueue(s, "x.y")
        claimed = await job_store.claim(s, "dead-worker", limit=1)
        claimed[0].locked_at = datetime.now(UTC) - timedelta(hours=1)
    async with sessions.begin() as s:
        assert await job_store.reclaim_stale(s, lease_seconds=60) == 1
    assert (await _state(sessions, job_id or 0)).state == JobState.QUEUED


async def test_worker_tick_success_failure_unknown(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    reg = Registry()
    seen: list[dict[str, object]] = []

    @reg.register("ok.job")
    async def ok(ctx: JobContext) -> None:
        seen.append(ctx.payload)

    @reg.register("bad.job")
    async def bad(ctx: JobContext) -> None:
        raise RuntimeError("source down")

    async with sessions.begin() as s:
        ok_id = await job_store.enqueue(s, "ok.job", {"n": 1})
        bad_id = await job_store.enqueue(s, "bad.job")
        unknown_id = await job_store.enqueue(s, "nope.job")

    result = await Worker(sessions, reg, _settings(), worker_id="t").tick()
    assert result.succeeded == [ok_id] and seen == [{"n": 1}]
    assert (await _state(sessions, ok_id or 0)).state == JobState.SUCCEEDED
    bad = await _state(sessions, bad_id or 0)
    assert bad.state == JobState.QUEUED and "source down" in (bad.last_error or "")
    assert (await _state(sessions, unknown_id or 0)).state == JobState.DEAD


async def test_kill_switch_blocks_publish_jobs(sessions: async_sessionmaker[AsyncSession]) -> None:
    reg = Registry()
    ran: list[str] = []

    @reg.register("publish.linkedin")
    async def publish(ctx: JobContext) -> None:
        ran.append("publish")

    @reg.register("scan.github")
    async def scan(ctx: JobContext) -> None:
        ran.append("scan")

    async with sessions.begin() as s:
        await job_store.enqueue(s, "publish.linkedin")
        await job_store.enqueue(s, "scan.github")
    # No kill_switch row => fail-safe ON: only non-publishing work runs.
    await Worker(sessions, reg, _settings(), worker_id="t").tick()
    assert ran == ["scan"]

    async with sessions.begin() as s:
        await settings_repo.put(s, settings_repo.KILL_SWITCH, {"on": False})
    await Worker(sessions, reg, _settings(), worker_id="t").tick()
    assert ran == ["scan", "publish"]


async def test_open_breaker_defers_without_spending_attempt(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    reg = Registry()

    @reg.register("news.rss")
    async def rss(ctx: JobContext) -> None:
        raise AssertionError("must not run while circuit is open")

    breaker = CircuitBreaker(failure_threshold=1)
    breaker.record_failure("news.rss")
    async with sessions.begin() as s:
        job_id = await job_store.enqueue(s, "news.rss")
    result = await Worker(sessions, reg, _settings(), breaker=breaker, worker_id="t").tick()
    job = await _state(sessions, job_id or 0)
    assert result.deferred == [job_id]
    assert job.state == JobState.QUEUED and job.attempts == 0


async def test_default_mode_is_shadow(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions() as s:
        assert await settings_repo.publish_mode(s) == PublishMode.SHADOW
        assert await settings_repo.kill_switch_on(s) is True
