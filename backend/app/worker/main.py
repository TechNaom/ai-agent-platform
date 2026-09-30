"""Worker loop: reclaim stale jobs, claim due jobs, run handlers, record outcomes.

Run with ``python -m app.worker.main``. Safe to run as several replicas.
"""

import asyncio
import contextlib
import logging
import os
import signal
import socket
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.content_engine.store import jobs as job_store
from app.content_engine.store import settings_repo
from app.content_engine.store.models import Job, JobState
from app.core.config import Settings, get_settings
from app.core.db import get_sessionmaker
from app.core.logging import configure_logging, correlation_id
from app.worker.breaker import CircuitBreaker
from app.worker.registry import (
    PUBLISH_PREFIX,
    JobContext,
    Registry,
    breaker_key,
    default_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class TickResult:
    reclaimed: int = 0
    succeeded: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)
    deferred: list[int] = field(default_factory=list)


class Worker:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        registry: Registry,
        settings: Settings,
        breaker: CircuitBreaker | None = None,
        worker_id: str | None = None,
    ) -> None:
        self.sessions = sessions
        self.registry = registry
        self.settings = settings
        self.breaker = breaker or CircuitBreaker()
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}"
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    async def tick(self) -> TickResult:
        result = TickResult()
        async with self.sessions.begin() as session:
            result.reclaimed = await job_store.reclaim_stale(
                session, lease_seconds=self.settings.job_lease_seconds
            )
            kill = await settings_repo.kill_switch_on(session)
            claimed = await job_store.claim(
                session,
                self.worker_id,
                limit=self.settings.worker_batch_size,
                exclude_types_prefix=PUBLISH_PREFIX if kill else None,
            )
            batch = [(j.id, j.type, dict(j.payload), j.attempts) for j in claimed]
        # Row locks are released here; long-running handlers never hold them.
        for job_id, job_type, payload, attempt in batch:
            await self._run_one(job_id, job_type, payload, attempt, result)
        return result

    async def _run_one(
        self,
        job_id: int,
        job_type: str,
        payload: dict[str, object],
        attempt: int,
        result: TickResult,
    ) -> None:
        key = breaker_key(job_type)
        token = correlation_id.set(f"job-{job_id}")
        try:
            if self.breaker.is_open(key):
                await self._defer(job_id, reason=f"circuit open for {key}")
                result.deferred.append(job_id)
                return
            handler = self.registry.get(job_type)
            if handler is None:
                await self._finish(job_id, error=f"no handler for {job_type!r}", dead=True)
                result.failed.append(job_id)
                return
            ctx = JobContext(job_id, job_type, dict(payload), attempt, self.sessions)
            try:
                await handler(ctx)
            except Exception as exc:  # handler failures are data, not crashes
                logger.exception("job failed", extra={"job_type": job_type})
                self.breaker.record_failure(key)
                await self._finish(job_id, error=f"{type(exc).__name__}: {exc}")
                result.failed.append(job_id)
            else:
                self.breaker.record_success(key)
                await self._finish(job_id)
                result.succeeded.append(job_id)
        finally:
            correlation_id.reset(token)

    async def _finish(self, job_id: int, *, error: str | None = None, dead: bool = False) -> None:
        async with self.sessions.begin() as session:
            job = await session.get(Job, job_id, with_for_update=True)
            if job is None:
                return
            if error is None:
                await job_store.complete(session, job)
            elif dead:
                job.state = JobState.DEAD
                job.last_error = error
            else:
                await job_store.fail(
                    session, job, error, backoff_base_seconds=self.settings.job_backoff_base_seconds
                )

    async def _defer(self, job_id: int, *, reason: str) -> None:
        """Put a job back without spending an attempt (its source is temporarily down)."""
        async with self.sessions.begin() as session:
            job = await session.get(Job, job_id, with_for_update=True)
            if job is None:
                return
            job.state = JobState.QUEUED
            job.attempts = max(job.attempts - 1, 0)
            job.locked_at = None
            job.last_error = reason
            job.run_after = datetime.now(UTC) + timedelta(seconds=self.breaker.cooldown_seconds)

    async def run_forever(self) -> None:
        logger.info("worker started", extra={"worker_id": self.worker_id})
        while not self._stop.is_set():
            try:
                result = await self.tick()
                if result.succeeded or result.failed or result.reclaimed:
                    logger.info(
                        "tick",
                        extra={
                            "succeeded": len(result.succeeded),
                            "failed": len(result.failed),
                            "reclaimed": result.reclaimed,
                        },
                    )
            except Exception:  # a bad tick (e.g. DB blip) must not kill the worker
                logger.exception("tick failed")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._stop.wait(), timeout=self.settings.worker_tick_seconds)
        logger.info("worker stopped")


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    worker = Worker(get_sessionmaker(), default_registry, settings)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, worker.stop)
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(_main())
