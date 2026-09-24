# PROJECT_STATE

Last updated: 2026-09-24 (foundation / scaffold pushed public for crash-safety).

## Objective

Build a production-grade, publicly playable **multi-agent + multi-RAG platform** with
first-class **evaluation** and **observability**, deployed to the cloud with guardrails.
Serves as the flagship portfolio piece for AI-product engineering (evals, RAG, agents,
observability, deployment).

## Architecture decisions (see docs/ARCHITECTURE.md for full rationale)

- **Backend:** FastAPI (async, streaming). **LLM:** Anthropic Claude — `claude-sonnet-5`
  for agents, `claude-haiku-4-5` for cheap paths, `claude-opus-4-8` for hardest;
  provider-abstracted. **Agent loop:** Anthropic SDK Tool Runner (no heavy framework).
- **RAG:** ChromaDB + hybrid retrieval + rerank (reuse `enterprise-knowledge-assistant`
  engine — do NOT duplicate it).
- **Observability & eval-scoring:** Langfuse.
- **Frontend:** React + Vite + Tailwind on Vercel. **Backend deploy:** Fly.io / Render.
- **Data:** real public datasets (defensible eval numbers).
- **Guardrails:** per-IP rate limits + hard monthly spend cap. **Rollout:** password-gated
  private beta → public. **Visibility:** GitHub repo is PUBLIC from day one.
- **Crash-safety mandate (user, 2026-09-24):** push to GitHub continuously — commit +
  push after every meaningful chunk, never hold work locally.

## The four agents

1. Research/answer (web_search) · 2. RAG Q&A (ChromaDB) · 3. Code review · 4. Data analysis (code_execution).

## Completed

- [x] Repo scaffolded on D drive (`/mnt/d/projects/ai-agent-platform`, `core.filemode false`).
- [x] Architecture + discovery docs, README, PROJECT_STATE, AI_HANDOFF.
- [x] Directory skeleton for backend/frontend/evals/obs/rag.
- [x] Public GitHub repo created + pushed (crash-safety baseline).

## Pending (build order)

1. **Backend skeleton** — FastAPI app, health check, model-selection layer, Anthropic client, streaming SSE endpoint.
2. **Agent 1 (Research)** — Tool Runner + web_search, streaming, Langfuse tracing. First end-to-end vertical slice.
3. **Observability wiring** — Langfuse traces on every run; trace ID in responses.
4. **Guardrails** — rate limiting + spend cap middleware (before any public exposure).
5. **Agent 2 (RAG Q&A)** — port the enterprise-knowledge-assistant retrieval engine; ingestion + corpus.
6. **Agent 3 (Code review)** and **Agent 4 (Data analysis)**.
7. **Eval harness** — offline CI-gated suite per agent on real public datasets; wire into CI.
8. **Frontend** — React panels per agent, live streaming, trace links.
9. **Deploy** — backend to Fly.io/Render, frontend to Vercel; private beta (password gate).
10. **Public launch** — flip the access toggle after cost/abuse validation.

## Next Recommended Task

Build the **backend skeleton + Research agent vertical slice** (items 1–3): a running
FastAPI service with one working, traced, streaming agent, so there is an end-to-end path
to demo before fanning out to the other three agents. Requires an `ANTHROPIC_API_KEY` and
a Langfuse project (cloud free tier is fine to start).

## Known open questions / risks

- Backend host final choice (Fly.io vs Render) — decide when first deploying.
- Real eval dataset selection per agent — pick freely-licensed sources at eval-harness time.
- Monthly spend cap value — set with the user before public launch.
