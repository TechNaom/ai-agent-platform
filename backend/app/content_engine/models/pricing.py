"""Per-model pricing (USD per 1M tokens). Verify against vendor docs before adding an
entry — prices change monthly (ADR-0003). A model with no entry cannot be routed to
(errors.UnknownModel): the router never makes an un-costed call.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float


# Verified 2026-09-30 against platform.claude.com (see docs/content-engine/ARCHITECTURE_PLAN.md).
# Low-cost provider entries are added as each is verified (ADR-0003); routes only reference
# models listed here.
PRICES: dict[str, Price] = {
    "claude-sonnet-5-5": Price(input_per_mtok=2.0, output_per_mtok=10.0),
    "claude-opus-5-5": Price(input_per_mtok=4.0, output_per_mtok=20.0),
    "claude-fable-5-1": Price(input_per_mtok=10.0, output_per_mtok=50.0),
    "claude-haiku-4-5": Price(input_per_mtok=1.0, output_per_mtok=5.0),
}


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    from app.content_engine.models.errors import UnknownModel

    price = PRICES.get(model)
    if price is None:
        raise UnknownModel(model)
    return (tokens_in / 1_000_000) * price.input_per_mtok + (
        tokens_out / 1_000_000
    ) * price.output_per_mtok
