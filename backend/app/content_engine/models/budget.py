"""Monthly LLM spend cap (owner default: $75/month). Checked before, recorded after, every call."""

from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_engine.store import settings_repo
from app.content_engine.store.models import Run

DEFAULT_CAP_USD = 75.0
BUDGET_SETTING_KEY = "llm_budget"


class BudgetGuard(Protocol):
    async def check(self) -> None:
        """Raise BudgetExceeded if the cap has already been reached."""
        ...

    async def record(self, cost_usd: float) -> None:
        """No-op by default: DB-backed guards record via the `runs` row instead."""
        ...


class NullBudgetGuard:
    """No cap enforced. Used only in tests / local calls with no DB session."""

    async def check(self) -> None:
        return

    async def record(self, cost_usd: float) -> None:
        return


class DatabaseBudgetGuard:
    """Sums `runs.cost_usd` for the current calendar month against a configurable cap."""

    def __init__(self, session: AsyncSession, *, default_cap_usd: float = DEFAULT_CAP_USD) -> None:
        self._session = session
        self._default_cap_usd = default_cap_usd

    async def _cap(self) -> float:
        value = await settings_repo.get(self._session, BUDGET_SETTING_KEY)
        return float((value or {}).get("monthly_cap_usd", self._default_cap_usd))

    async def _spent_this_month(self) -> float:
        now = datetime.now(UTC)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.coalesce(func.sum(Run.cost_usd), 0)).where(Run.started_at >= start)
        return float((await self._session.execute(stmt)).scalar_one())

    async def check(self) -> None:
        from app.content_engine.models.errors import BudgetExceeded

        cap = await self._cap()
        spent = await self._spent_this_month()
        if spent >= cap:
            raise BudgetExceeded(spent, cap)

    async def record(self, cost_usd: float) -> None:
        # Spend is derived from `runs` rows written by the caller (router.complete() returns
        # cost; the caller persists a Run). No separate write here avoids double-counting.
        return
