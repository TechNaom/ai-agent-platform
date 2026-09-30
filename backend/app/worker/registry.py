"""Job-type → handler registry. Handlers are async, idempotent, and open their own sessions."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Job types starting with this prefix publish content; the kill switch blocks them.
PUBLISH_PREFIX = "publish."


@dataclass(frozen=True)
class JobContext:
    job_id: int
    job_type: str
    payload: dict[str, Any]
    attempt: int
    sessions: async_sessionmaker[AsyncSession]


Handler = Callable[[JobContext], Awaitable[None]]


@dataclass
class Registry:
    handlers: dict[str, Handler] = field(default_factory=dict)

    def register(self, job_type: str) -> Callable[[Handler], Handler]:
        def decorator(fn: Handler) -> Handler:
            if job_type in self.handlers:
                raise ValueError(f"handler already registered for {job_type!r}")
            self.handlers[job_type] = fn
            return fn

        return decorator

    def get(self, job_type: str) -> Handler | None:
        return self.handlers.get(job_type)


def breaker_key(job_type: str) -> str:
    """Jobs share a circuit breaker per source family, e.g. ``publish.linkedin``."""
    parts = job_type.split(".")
    return ".".join(parts[:2])


default_registry = Registry()
