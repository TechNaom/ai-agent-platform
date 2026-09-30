"""Async database engine and session factory."""

from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine | None:
    url = get_settings().database_url
    if url is None:
        return None
    return create_async_engine(url.get_secret_value(), pool_pre_ping=True)


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine = get_engine()
    if engine is None:
        raise RuntimeError("DATABASE_URL is not set")
    return async_sessionmaker(engine, expire_on_commit=False)


async def ping_database() -> bool:
    """True if the database answers ``SELECT 1``; False if unreachable or not configured."""
    engine = get_engine()
    if engine is None:
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # any driver/network failure means "not ready"
        return False
    return True
