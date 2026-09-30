"""The model router: agent -> ordered provider/model chain, with retry, fallback, cost and
budget enforcement (ADR-0003). This is the only place agent code calls an LLM through.
"""

import logging

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.content_engine.models.budget import BudgetGuard, NullBudgetGuard
from app.content_engine.models.errors import AllProvidersFailed, ProviderError
from app.content_engine.models.pricing import cost_usd
from app.content_engine.models.providers.base import Provider
from app.content_engine.models.routes import DEFAULT_ROUTES, AgentName
from app.content_engine.models.types import CallSpec, CompletionResult, ModelChoice, RoutedResult

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, ProviderError) and exc.retryable


class ModelRouter:
    def __init__(
        self,
        providers: dict[str, Provider],
        routes: dict[AgentName, list[ModelChoice]] | None = None,
        budget: BudgetGuard | None = None,
        *,
        retry_attempts: int = 3,
    ) -> None:
        self._providers = providers
        self._routes = routes or DEFAULT_ROUTES
        self._budget = budget or NullBudgetGuard()
        self._retry_attempts = retry_attempts

    async def complete(self, agent: AgentName, spec: CallSpec) -> RoutedResult:
        chain = self._routes.get(agent)
        if not chain:
            raise ValueError(f"no route configured for agent {agent!r}")

        await self._budget.check()

        errors: list[ProviderError] = []
        for attempt, choice in enumerate(chain, start=1):
            provider = self._providers.get(choice.provider)
            if provider is None:
                errors.append(
                    ProviderError(
                        choice.provider,
                        choice.model,
                        "provider not configured",
                        retryable=False,
                    )
                )
                continue
            try:
                completion = await self._call_with_retry(provider, choice, spec)
            except ProviderError as exc:
                logger.warning(
                    "provider failed, trying next in chain",
                    extra={
                        "agent": agent.value,
                        "provider": choice.provider,
                        "model": choice.model,
                    },
                )
                errors.append(exc)
                continue

            cost = cost_usd(choice.model, completion.tokens_in, completion.tokens_out)
            await self._budget.record(cost)
            return RoutedResult(
                completion=completion, choice=choice, cost_usd=cost, attempt=attempt
            )

        raise AllProvidersFailed(agent.value, errors)

    async def _call_with_retry(
        self, provider: Provider, choice: ModelChoice, spec: CallSpec
    ) -> CompletionResult:
        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential_jitter(initial=1, max=20),
            reraise=True,
        )
        async def _call() -> CompletionResult:
            return await provider.complete(model=choice.model, spec=spec)

        return await _call()
