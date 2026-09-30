# AI_HANDOFF

For a different AI assistant (or a fresh session) picking this repo up cold.

## What this is

An enterprise-style AI platform with first-class **evaluation** and **observability**, and
two products:

1. **Content engine (current focus):** an autonomous, multi-channel content system that
   builds the Manohar Papasani AI-centric personal brand from the whole TechNaom GitHub
   account plus AI news. Read `docs/content-engine/ARCHITECTURE_PLAN.md`, then
   `docs/content-engine/AGENT_MEMORY.md`.
2. **Interactive agent platform (later):** 4 public demo agents. Read `docs/ARCHITECTURE.md`.

Then read `docs/adr/` (decisions) and `PROJECT_STATE.md` (status + next task).

## Design philosophy

- **Evals and observability are load-bearing.** Every agent run is traced in Langfuse.
  Every agent has an eval set, and CI blocks regressions.
- **Framework-light.** No LangGraph/CrewAI. Plain Python and a thin model router (ADR-0003).
- **Deterministic control, LLM judgment** (ADR-0007).
- **Skip, don't publish** when in doubt. There is a brand under this.
- **Authenticity rule:** never fabricate first-person experiences or metrics in content.

## Conventions

- Repo is on the Windows D drive (`/mnt/d/projects/ai-agent-platform`); `core.filemode false`.
- **Work via issue → branch → PR → green CI → squash-merge.** `main` is protected. See `CONTRIBUTING.md`.
- **Push continuously.** This is the owner's crash-safety mandate. The repo is PUBLIC:
  never commit secrets, drafts, analytics or backups. Those go to the private
  `technaom-content-vault` repo.
- Python 3.12, ruff, mypy strict, pytest. Code lives under `backend/app/`, and the content
  engine under `backend/app/content_engine/`.
- Current Claude IDs (verified 2026-09-30): `claude-sonnet-5-5`, `claude-opus-5-5`,
  `claude-fable-5-1`, `claude-haiku-4-5`. Re-verify model IDs before use; they change monthly.
- Build sessions should run on Sonnet (owner preference, cost).

## What NOT to change / duplicate

- Don't give agents private memory stores (ADR-0002).
- Don't make the scheduler an LLM or move scheduling to external cron (ADR-0004, ADR-0007).
- Don't re-implement the RAG engine: port it from `TechNaom/enterprise-knowledge-assistant`.
- Don't port `linkedin-news-agent` wholesale. Reuse its LinkedIn client, Tavily client,
  critique gate and token-expiry checker.

## Current task / next task

See `PROJECT_STATE.md` → "Next Recommended Task" and the GitHub milestones and issues.
