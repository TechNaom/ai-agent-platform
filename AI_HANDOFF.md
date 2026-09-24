# AI_HANDOFF

For a different AI assistant (or a fresh session) picking this repo up cold.

## What this is

A production, publicly-playable **multi-agent + multi-RAG platform** with first-class
**evaluation** and **observability**. Portfolio flagship for AI-product engineering. Not a
course, not a toy demo. Read `docs/ARCHITECTURE.md` first, then `PROJECT_STATE.md` for
current status and the "Next Recommended Task".

## Design philosophy

- **Evals and observability are load-bearing subsystems**, not afterthoughts. Every agent
  run is traced (Langfuse) and covered by an offline, CI-gated eval on a real public dataset.
- **Framework-light agent code.** Use the Anthropic SDK Tool Runner
  (`client.beta.messages.tool_runner`) for the agent loop — readable, minimal, no
  LangGraph/CrewAI dependency. Teach/show the concept in plain code.
- **Real, defensible numbers.** Eval datasets are real and public, not synthetic.
- **Guardrails before public.** Rate limits + hard monthly spend cap are required before
  any public exposure; agents run least-privilege.

## Conventions

- Repo lives on the Windows D drive (`/mnt/d/projects/ai-agent-platform`); `git config
  core.filemode false` is set (drvfs reports 777 otherwise). Existing sibling course repos
  live under `/home/dell/projects` — this project is intentionally on D.
- **Push to GitHub continuously** — the user's explicit crash-safety requirement. Commit +
  push after every meaningful chunk; never leave work only local. Repo is PUBLIC.
- Model IDs are current as of 2026-09: `claude-sonnet-5`, `claude-haiku-4-5`,
  `claude-opus-4-8`. Adaptive thinking only (no `budget_tokens`); control depth with
  `effort`. Stream large-`max_tokens` requests.

## What NOT to change / duplicate

- Don't re-implement the advanced-RAG engine from scratch — port/reuse the one already
  built in `TechNaom/enterprise-knowledge-assistant` (hybrid retrieval, RRF, LLM rerank,
  MMR, citations).
- Don't add a heavy agent framework as a required dependency.
- Don't expose the platform publicly without the rate-limit + spend-cap guardrails in place.

## Current task / next task

See `PROJECT_STATE.md` → "Next Recommended Task". As of this handoff: build the backend
skeleton + Research-agent vertical slice (running FastAPI service, one traced streaming
agent), then fan out to the other three agents, then evals, then frontend, then deploy.

## Key architectural decisions

Summarized in `PROJECT_STATE.md` → Architecture decisions; full rationale in
`docs/ARCHITECTURE.md`.
