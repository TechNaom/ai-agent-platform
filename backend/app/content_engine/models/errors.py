"""Router error hierarchy. Provider adapters must raise these, not leak SDK exceptions."""


class ProviderError(Exception):
    """A single provider call failed; the router may try the next choice in the chain."""

    def __init__(self, provider: str, model: str, message: str, *, retryable: bool) -> None:
        super().__init__(f"{provider}/{model}: {message}")
        self.provider = provider
        self.model = model
        self.retryable = retryable


class AllProvidersFailed(Exception):
    """Every choice in an agent's fallback chain failed."""

    def __init__(self, agent: str, errors: list[ProviderError]) -> None:
        detail = "; ".join(str(e) for e in errors)
        super().__init__(f"all providers failed for agent {agent!r}: {detail}")
        self.agent = agent
        self.errors = errors


class BudgetExceeded(Exception):
    """The monthly LLM spend cap (settings key `llm_budget`) has been reached."""

    def __init__(self, spent_usd: float, cap_usd: float) -> None:
        super().__init__(f"spend ${spent_usd:.2f} has reached the ${cap_usd:.2f} cap")
        self.spent_usd = spent_usd
        self.cap_usd = cap_usd


class UnknownModel(Exception):
    """A model has no pricing entry; refusing to make an un-costed call."""

    def __init__(self, model: str) -> None:
        super().__init__(f"no pricing entry for model {model!r} — add one before routing to it")
