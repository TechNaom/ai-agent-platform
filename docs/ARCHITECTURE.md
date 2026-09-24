# Architecture

This document is the authoritative design + rationale. Update it as decisions change.

## Goal & positioning

A **production multi-agent + multi-RAG platform** that is publicly playable, with
**evaluation and observability as first-class, load-bearing subsystems** — not a demo,
not a course. The interview/portfolio thesis: *"here are real agents; here is the eval
harness that proves they work; here is the observability that shows how they behave in
production; here it is deployed and open to the public with guardrails."*

This is distinct from the sibling course repos and from `enterprise-knowledge-assistant`
(a single-RAG Streamlit capstone with no evals/observability/multi-agent/public UI —
its advanced-RAG engine is a **component to reuse here**, not something to duplicate).

## The four agents

Each agent = a system prompt + a tool set, driven by a shared lightweight agent runtime.

| Agent | Core capability | Tools | Real eval dataset |
|---|---|---|---|
| **Research** | Plan → search → synthesize with citations | `web_search` (Anthropic server tool) | multi-hop QA benchmark (e.g. HotpotQA subset) |
| **RAG Q&A** | Grounded answers over a corpus | retrieval over ChromaDB (hybrid + rerank) | QA-over-docs benchmark + curated corpus |
| **Code review** | Structured review: issues, severity, fixes | none (reasoning) / optional static-analysis tool | curated set of known-buggy snippets |
| **Data analysis** | Explore CSV, answer, chart | `code_execution` (Anthropic server tool) | public datasets with known ground-truth answers |

## Backend

- **FastAPI**, async, streaming responses (SSE) so the UI renders tokens live.
- **Anthropic SDK** (`anthropic`). Model policy:
  - Agents: `claude-sonnet-5` (best quality/cost balance for agentic work; intro pricing through 2026-08-31).
  - Cheap/fast paths (classification, routing, short answers): `claude-haiku-4-5`.
  - Hardest reasoning if needed: `claude-opus-4-8`.
  - Wrapped behind a thin model-selection layer so the provider/model is swappable.
- **Agent runtime:** the SDK **Tool Runner** (`client.beta.messages.tool_runner`) drives
  the perceive→reason→act→observe loop. Keeps code readable and framework-light
  (matches the house philosophy of teaching concepts with minimal code); no LangGraph/
  CrewAI dependency required.
- **Adaptive thinking** (`thinking={"type":"adaptive"}`) + `effort` tuned per agent.

## RAG subsystem

- **ChromaDB** persistent store. Reuse the advanced-retrieval design already proven in
  `enterprise-knowledge-assistant`: hybrid dense + BM25 with RRF fusion, multi-query
  expansion, LLM re-ranking, MMR diversification, grounded answers with `[n]` citations.
- Ingestion pipeline: load (PDF/MD/TXT) → chunk → embed → index.

## Observability (spine)

- **Langfuse** — every agent run emits a trace: each step, tool call, token counts,
  cost, latency, and (where applicable) an eval score. Self-hostable via Docker, or the
  cloud free tier for the demo.
- Trace IDs surfaced in the UI so a run can be inspected end-to-end.

## Evaluation (spine)

- **Offline (CI-gated):** `backend/app/evals/` runs each agent against a real public
  dataset and computes task-appropriate metrics (retrieval quality for RAG, task-success
  / answer-match for research & data analysis, bug-detection recall/precision for code
  review). Wired into `.github/workflows/` so regressions block merges.
- **Online:** Langfuse scores live traces (heuristics + LLM-as-judge) for continuous
  quality monitoring.
- Datasets are **real and public** (freely licensed) so numbers are defensible.

## Frontend

- **React + Vite + Tailwind** SPA. One panel per agent; live token streaming; shows the
  agent's steps/tool-calls and a link to the Langfuse trace.
- Deployed on **Vercel**.

## Deployment (cloud)

- Frontend → Vercel (free tier).
- Backend (FastAPI) → Fly.io or Render (small paid instance acceptable).
- Vector DB → ChromaDB persisted to a volume on the backend host.
- Langfuse → cloud free tier initially; self-host later if needed.

## Guardrails, cost & abuse control (required before public)

- **Per-IP / per-session rate limits** (e.g. `slowapi`) on every agent endpoint.
- **Hard monthly spend cap** — server tracks cumulative token spend and refuses new runs
  past the cap; surfaces a friendly "demo limit reached" message.
- **Prompt-injection & abuse posture** — agents run with least-privilege tools; no
  secrets in prompts; inputs size-limited.
- **Access rollout:** password/invite-gated **private beta** first (dogfood, watch real
  cost-per-session and abuse patterns), then flip to fully public — same infra, a toggle.

## Model / provider facts (verified via claude-api skill, 2026-09-24)

- `claude-sonnet-5`: $3/$15 per MTok (intro $2/$10 through 2026-08-31), 1M context, 128K out.
- `claude-haiku-4-5`: $1/$5 per MTok, 200K context.
- `claude-opus-4-8`: $5/$25 per MTok, 1M context.
- Adaptive thinking only on current models (`budget_tokens` is rejected); control depth with `effort`.
- Stream any request with large `max_tokens` to avoid HTTP timeouts.
