# ADR-0003: Provider-neutral model routing (premium + low-cost)

- Status: Accepted · 2026-09-30
- Partially supersedes the "Anthropic Tool Runner only" choice in docs/ARCHITECTURE.md
  for the content engine.

## Context
The owner wants low-cost models (Grok, Llama, etc.) where they are good enough. Volume
is dominated by bulk work (news triage, repo summarisation, channel adaptation), while
brand risk is concentrated in writing, fact-checking and judging.

## Decision
- A thin model router maps **agent → (provider, model)** via config, with ordered fallbacks.
- Transport: the Anthropic SDK for Claude; an OpenAI-compatible client (OpenRouter / Groq /
  xAI) for everything else. Tool calling uses each SDK's native format behind one interface.
- Defaults: cheap models for News triage, bulk repo summarisation, Channel Adapter and
  Engagement Analyst. Claude for Writer, Fact-Checker, Brand & Quality Judge and Visual QA.
  The Judge runs on a **different model family** from the Writer.
- **Evals decide.** Each agent's eval set runs across candidate models, and the cheapest
  model that passes its threshold wins. The choice is recorded in config with the eval run ID.
- Web search goes through Tavily (provider-neutral), not a vendor server tool.
- Model IDs are verified against vendor docs at implementation time (they change monthly).

## Consequences
- Cost control without betting the brand on the cheapest model.
- The router is itself a portfolio artefact ("cut cost X% at equal eval scores").
- Slightly more code than a single-vendor Tool Runner loop.
