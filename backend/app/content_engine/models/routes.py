"""Agent -> model fallback chains (ADR-0003).

Low-cost entries use placeholder model ids pending pricing.PRICES verification with real
provider access (issue #5 note); until verified, those agents fall back to Claude Haiku so
nothing is ever routed to an un-costed model. Update alongside pricing.py once confirmed.
"""

from enum import StrEnum

from app.content_engine.models.types import ModelChoice

CLAUDE_SONNET = ModelChoice("anthropic", "claude-sonnet-5-5")
CLAUDE_OPUS = ModelChoice("anthropic", "claude-opus-5-5")
CLAUDE_HAIKU = ModelChoice("anthropic", "claude-haiku-4-5")


class AgentName(StrEnum):
    """The 10 LLM agents (plan §4.4)."""

    REPO_KNOWLEDGE_MAPPER = "repo_knowledge_mapper"
    CONTENT_STRATEGIST = "content_strategist"
    NEWS_SCOUT_ANALYST = "news_scout_analyst"
    WRITER = "writer"
    CAROUSEL_DESIGNER = "carousel_designer"
    CHANNEL_ADAPTER = "channel_adapter"
    FACT_CHECKER = "fact_checker"
    QUALITY_JUDGE = "quality_judge"
    VISUAL_QA = "visual_qa"
    ENGAGEMENT_ANALYST = "engagement_analyst"


# Cheapest-first chains for bulk/low-risk agents; quality-critical agents go straight to
# Claude and never fall back to an unverified cheap model mid-chain.
DEFAULT_ROUTES: dict[AgentName, list[ModelChoice]] = {
    AgentName.REPO_KNOWLEDGE_MAPPER: [CLAUDE_HAIKU, CLAUDE_SONNET],
    AgentName.CONTENT_STRATEGIST: [CLAUDE_SONNET],
    AgentName.NEWS_SCOUT_ANALYST: [CLAUDE_HAIKU, CLAUDE_SONNET],
    AgentName.WRITER: [CLAUDE_SONNET],
    AgentName.CAROUSEL_DESIGNER: [CLAUDE_SONNET],
    AgentName.CHANNEL_ADAPTER: [CLAUDE_HAIKU, CLAUDE_SONNET],
    AgentName.FACT_CHECKER: [CLAUDE_SONNET],
    # Judge should ideally run on a different model family from the Writer (ADR-0003);
    # both currently resolve to Claude until a verified second-family route is added.
    AgentName.QUALITY_JUDGE: [CLAUDE_SONNET],
    AgentName.VISUAL_QA: [CLAUDE_SONNET],
    AgentName.ENGAGEMENT_ANALYST: [CLAUDE_HAIKU],
}
