# PROJECT_STATE

Last updated: 2026-09-30 (Sprint 0: enterprise foundation).

## Objective

A production-grade AI platform with first-class **evaluation** and **observability**,
run like a software-company codebase. Two products share one kernel:

1. **Content engine (building first).** An autonomous, multi-channel, AI-centric content
   system whose purpose is building the **Manohar Papasani** brand (GenAI Solution
   Architect & AI Systems Builder). It turns the whole TechNaom GitHub account into
   500–1,000+ posts and carousels, adds a ranked AI-news stream, and publishes to
   LinkedIn and other channels in waves. Plan: `docs/content-engine/ARCHITECTURE_PLAN.md`.
2. **Interactive agent platform (after).** Four public demo agents (Research, RAG Q&A,
   Code review, Data analysis) with a React UI. Design: `docs/ARCHITECTURE.md`.

## Architecture decisions (see `docs/adr/`)

- ADR-0002: one shared agent memory, Postgres + pgvector (Neon). Agents are stateless;
  context builders load memory (`docs/content-engine/AGENT_MEMORY.md`).
- ADR-0003: provider-neutral model routing. Claude for Writer, Fact-Checker, Judge and
  Visual QA; low-cost models (Grok, Groq/OpenRouter) for bulk work. Evals pick the
  cheapest model that passes.
- ADR-0004: Fly.io (`api` + `worker`), DB-backed in-app scheduler, GitHub Actions as
  watchdog and backup runner. Frontend on GitHub Pages.
- ADR-0005: SHADOW → VETO → AUTONOMOUS, plus a kill switch.
- ADR-0006: public code repo; private `TechNaom/technaom-content-vault` for content and backups.
- ADR-0007: deterministic orchestrator; 10 LLM agents for judgment only.
- Owner defaults (2026-09-30): $75/month LLM cap; posts at 08:30 and 18:30 IST.
- **Crash-safety mandate:** everything is pushed to GitHub continuously.

## Completed

- [x] Foundation docs, repo skeleton, public repo (2026-09-24).
- [x] Content engine architecture plan approved (2026-09-30).
- [x] Sprint 0: CONTRIBUTING, SECURITY, CI (ruff, mypy, pytest, gitleaks), Dependabot,
      CODEOWNERS, issue/PR templates, pre-commit, 7 ADRs, agent memory design.

## Sprint plan (GitHub milestones)

| Milestone | Scope |
|---|---|
| Sprint 0 | Enterprise foundation (this sprint) |
| Sprint 1 | Foundation: config, DB schema + migrations, job queue + worker, model router, Langfuse, GitHub scanner, Docker, Fly deploy, watchdog + backups |
| Sprint 2 | GitHub content engine: knowledge map, strategist, writer, dedup, judge, fact-check, evals, SHADOW digest |
| Sprint 3 | Carousel pipeline |
| Sprint 4 | News engine |
| Sprint 5 | Editorial engine |
| Sprint 6 | Publishing wave 1: LinkedIn, blog, Slack, Telegram, Discord |
| Later | Waves 2–4 (X, Bluesky, Dev.to · Meta · WhatsApp), learning loop, the 4 demo agents |

## Next Recommended Task

**Sprint 1, first issue:** backend skeleton (settings, FastAPI `api` with `/health`,
Postgres schema + Alembic migrations, job table + worker tick loop). Needs from the owner:
a Neon Postgres URL, an Anthropic key, a Groq key and Langfuse keys, set as secrets
(never pasted in chat).

## Known open questions / risks

- LinkedIn API: document (carousel) posts and member analytics availability for personal
  profiles are unverified. This is Phase 0 spike work in Sprint 1.
- Meta app review (Facebook, Instagram, Threads) can take weeks. Apply early.
- Exact low-cost model IDs are chosen by evals at implementation time.
- Session model: build work should run on Sonnet (owner preference).
