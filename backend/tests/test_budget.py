"""DatabaseBudgetGuard against real Postgres: sums `runs.cost_usd` for the current month."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_engine.models.budget import DatabaseBudgetGuard
from app.content_engine.models.errors import BudgetExceeded
from app.content_engine.store import settings_repo
from app.content_engine.store.models import Run, RunStatus

pytestmark = pytest.mark.db


async def test_check_passes_when_under_cap(session: AsyncSession) -> None:
    session.add(Run(pipeline="writer", status=RunStatus.SUCCEEDED, cost_usd=Decimal("1.00")))
    await session.flush()
    await DatabaseBudgetGuard(session, default_cap_usd=75.0).check()  # no raise


async def test_check_raises_when_cap_reached(session: AsyncSession) -> None:
    session.add(Run(pipeline="writer", status=RunStatus.SUCCEEDED, cost_usd=Decimal("80.00")))
    await session.flush()
    with pytest.raises(BudgetExceeded) as exc_info:
        await DatabaseBudgetGuard(session, default_cap_usd=75.0).check()
    assert exc_info.value.spent_usd == pytest.approx(80.0)


async def test_cap_is_configurable_via_settings(session: AsyncSession) -> None:
    session.add(Run(pipeline="writer", status=RunStatus.SUCCEEDED, cost_usd=Decimal("10.00")))
    await settings_repo.put(session, "llm_budget", {"monthly_cap_usd": 5.0})
    await session.flush()
    with pytest.raises(BudgetExceeded) as exc_info:
        await DatabaseBudgetGuard(session).check()
    assert exc_info.value.cap_usd == pytest.approx(5.0)
