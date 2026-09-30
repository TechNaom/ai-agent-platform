"""Alembic environment (async). The URL is read from DATABASE_URL only."""

import asyncio
from typing import Any

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.content_engine.store.models import Base
from app.core.config import get_settings

target_metadata = Base.metadata

# Indexes created by hand in migrations (e.g. HNSW with opclasses) that autogenerate
# can't represent. Skipped during model/DB comparison.
MANUAL_INDEX_PREFIX = "ix_hnsw_"


def include_object(
    obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
) -> bool:
    return not (type_ == "index" and name is not None and name.startswith(MANUAL_INDEX_PREFIX))


def _url() -> str:
    url = get_settings().database_url
    if url is None:
        raise RuntimeError("DATABASE_URL is not set")
    return url.get_secret_value()


def _configure(connection: Connection | None = None, **kw: Any) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        **kw,
    )


def run_migrations_offline() -> None:
    _configure(url=_url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection: Connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(_url())
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
