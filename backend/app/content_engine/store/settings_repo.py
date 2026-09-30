"""Runtime switches stored in the ``settings`` table (kill switch, publish mode)."""

from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_engine.store.models import PublishMode, Setting

KILL_SWITCH = "kill_switch"
MODE = "mode"


async def get(session: AsyncSession, key: str) -> dict[str, Any] | None:
    row = await session.get(Setting, key)
    return row.value if row else None


async def put(session: AsyncSession, key: str, value: dict[str, Any]) -> None:
    stmt = insert(Setting).values(key=key, value=value)
    stmt = stmt.on_conflict_do_update(index_elements=[Setting.key], set_={"value": value})
    await session.execute(stmt)


async def kill_switch_on(session: AsyncSession) -> bool:
    """Fail safe: publishing is allowed only when the switch is explicitly off."""
    value = await get(session, KILL_SWITCH)
    return True if value is None else bool(value.get("on", True))


async def publish_mode(session: AsyncSession) -> PublishMode:
    """Defaults to SHADOW (ADR-0005): nothing goes live unless configured."""
    value = await get(session, MODE)
    return PublishMode((value or {}).get("mode", PublishMode.SHADOW))
