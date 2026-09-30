"""Shared fixtures. DB tests run only where DATABASE_URL points at Postgres (CI)."""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        trans = await conn.begin()
        async with async_sessionmaker(bind=conn, expire_on_commit=False)() as s:
            yield s
        await trans.rollback()  # every test leaves the DB untouched
    await engine.dispose()
