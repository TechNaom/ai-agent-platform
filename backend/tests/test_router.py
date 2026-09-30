"""Model router: fallback chains, retry, budget enforcement, cost accounting.

Uses a fake Provider — no network calls, no API keys needed.
"""

from dataclasses import dataclass, field

import pytest

from app.content_engine.models.errors import (
    AllProvidersFailed,
    BudgetExceeded,
    ProviderError,
    UnknownModel,
)
from app.content_engine.models.pricing import PRICES, cost_usd
from app.content_engine.models.router import ModelRouter
from app.content_engine.models.routes import AgentName
from app.content_engine.models.types import CallSpec, Message, ModelChoice, Role

FAST = ModelChoice("fake", "fast-model")
STRONG = ModelChoice("fake", "strong-model")
PRICES["fast-model"] = PRICES["claude-haiku-4-5"]
PRICES["strong-model"] = PRICES["claude-sonnet-5-5"]

SPEC = CallSpec(system="be helpful", messages=(Message(Role.USER, "hi"),))


@dataclass
class FakeProvider:
    name: str
    fail_times: int = 0  # number of calls that raise before one succeeds
    retryable: bool = True
    text: str = "ok"
    calls: list[str] = field(default_factory=list)

    async def complete(self, *, model, spec):  # type: ignore[no-untyped-def]
        self.calls.append(model)
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ProviderError(self.name, model, "boom", retryable=self.retryable)
        from app.content_engine.models.types import CompletionResult

        return CompletionResult(
            text=self.text, tool_calls=(), tokens_in=100, tokens_out=50,
            stop_reason="end_turn", raw_model=model,
        )


def router_with(  # type: ignore[no-untyped-def]
    provider: FakeProvider, agent: AgentName = AgentName.WRITER, **kw
):
    routes = {agent: [FAST, STRONG]}
    return ModelRouter({"fake": provider}, routes=routes, **kw)


async def test_succeeds_on_first_choice() -> None:
    provider = FakeProvider("fake")
    router = router_with(provider)
    result = await router.complete(AgentName.WRITER, SPEC)
    assert result.choice == FAST and result.attempt == 1
    assert provider.calls == ["fast-model"]


async def test_retries_transient_failure_then_succeeds() -> None:
    provider = FakeProvider("fake", fail_times=2, retryable=True)
    router = router_with(provider, retry_attempts=3)
    result = await router.complete(AgentName.WRITER, SPEC)
    assert result.attempt == 1  # same choice, retried within the provider call
    assert len(provider.calls) == 3


async def test_falls_back_to_next_choice_when_retries_exhausted() -> None:
    fast = FakeProvider("fake", fail_times=99, retryable=True)
    strong = FakeProvider("fake2")
    routes = {AgentName.WRITER: [FAST, STRONG]}
    router = ModelRouter({"fake": fast, "fake2": strong}, routes=routes, retry_attempts=2)
    result = await router.complete(AgentName.WRITER, SPEC)
    assert result.choice == STRONG and result.attempt == 2


async def test_non_retryable_failure_skips_straight_to_next_choice() -> None:
    fast = FakeProvider("fake", fail_times=1, retryable=False)
    strong = FakeProvider("fake2")
    routes = {AgentName.WRITER: [FAST, STRONG]}
    router = ModelRouter({"fake": fast, "fake2": strong}, routes=routes, retry_attempts=5)
    result = await router.complete(AgentName.WRITER, SPEC)
    assert result.choice == STRONG
    assert fast.calls == ["fast-model"]  # not retried 5 times — failed fast


async def test_all_providers_failed_raised_with_all_errors() -> None:
    fast = FakeProvider("fake", fail_times=99)
    strong = FakeProvider("fake2", fail_times=99)
    routes = {AgentName.WRITER: [FAST, STRONG]}
    router = ModelRouter({"fake": fast, "fake2": strong}, routes=routes, retry_attempts=1)
    with pytest.raises(AllProvidersFailed) as exc_info:
        await router.complete(AgentName.WRITER, SPEC)
    assert len(exc_info.value.errors) == 2


async def test_missing_provider_in_registry_falls_back() -> None:
    strong = FakeProvider("fake2")
    routes = {AgentName.WRITER: [FAST, STRONG]}
    router = ModelRouter({"fake2": strong}, routes=routes)  # "fake" not registered
    result = await router.complete(AgentName.WRITER, SPEC)
    assert result.choice == STRONG


async def test_no_route_configured_raises() -> None:
    router = ModelRouter({}, routes={})
    with pytest.raises(ValueError, match="no route"):
        await router.complete(AgentName.WRITER, SPEC)


async def test_cost_is_computed_from_pricing_table() -> None:
    provider = FakeProvider("fake")
    router = router_with(provider)
    result = await router.complete(AgentName.WRITER, SPEC)
    expected = cost_usd("fast-model", 100, 50)
    assert result.cost_usd == pytest.approx(expected)
    assert expected > 0


def test_unknown_model_refuses_to_cost() -> None:
    with pytest.raises(UnknownModel):
        cost_usd("no-such-model", 1, 1)


async def test_budget_guard_blocks_before_any_call() -> None:
    class AlwaysOver:
        async def check(self) -> None:
            raise BudgetExceeded(100.0, 75.0)

        async def record(self, cost_usd: float) -> None:
            return

    provider = FakeProvider("fake")
    router = router_with(provider, budget=AlwaysOver())
    with pytest.raises(BudgetExceeded):
        await router.complete(AgentName.WRITER, SPEC)
    assert provider.calls == []  # never called: checked before any provider touch
