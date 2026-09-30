# AI Agent Platform

A production-grade, publicly playable platform hosting **multiple useful AI agents** and
**multiple RAG pipelines**, built to enterprise standards with **first-class evaluation
and observability**. This is the flagship portfolio project for demonstrating real
AI-product engineering: agent design, RAG, evals, observability, cost/latency control,
and public deployment.

> **Status:** Sprint 0 (enterprise foundation). Two products: the interactive agent
> platform and the multi-channel **content engine** (`docs/content-engine/`). See [`PROJECT_STATE.md`](PROJECT_STATE.md) for the
> live build status and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design.

## What it does

Four genuinely useful agents, each usable from a public React UI:

1. **Research / answer agent** — multi-step web research that plans, searches, and cites sources.
2. **Document / RAG Q&A agent** — grounded question-answering over a document corpus (builds on advanced RAG: hybrid retrieval, re-ranking, citations).
3. **Code review / debugging agent** — paste code or a snippet; get a structured review with issues, severities, and fixes.
4. **Data analysis agent** — upload a CSV; the agent explores it, answers questions, and generates charts.

Cutting across all four:

- **Evaluation** — an offline, CI-gated regression suite over real public datasets, plus online eval-scoring of live traces.
- **Observability** — every agent run is traced (steps, tool calls, tokens, cost, latency) via Langfuse.
- **Guardrails** — per-IP/session rate limits and a hard monthly spend cap, so public access can't run up the bill or be abused.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI (async, streaming) |
| LLM | Provider-neutral router (ADR-0003): Claude (`claude-sonnet-5-5`, `claude-opus-5-5`, `claude-haiku-4-5`) for quality-critical work; low-cost models (Grok, Groq-hosted open models via OpenRouter) where evals allow |
| Agent loop | Anthropic SDK Tool Runner (lightweight, no heavy framework) |
| RAG | ChromaDB (persistent) + hybrid retrieval + re-ranking |
| Observability & eval scoring | Langfuse (self-hosted or cloud free tier) |
| Frontend | React + Vite + Tailwind |
| Deploy | Frontend: GitHub Pages · Backend + worker: Fly.io (ADR-0004) · DB: Neon Postgres + pgvector |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full rationale, and
[`AI_HANDOFF.md`](AI_HANDOFF.md) for cold-pickup context.

## Repository layout

```
backend/        FastAPI app: agents, RAG, observability, evals
  app/agents/     one module per agent (research, rag_qa, code_review, data_analysis)
  app/rag/        ingestion + retrieval
  app/obs/        Langfuse tracing wiring
  app/evals/      offline eval harness (CI-gated)
  datasets/       real public eval datasets (or fetch scripts)
frontend/       React + Vite + Tailwind SPA
scripts/        local dev + eval runners
docs/           architecture, discovery notes
quality-audits/ per-milestone quality reviews
```

## License

TBD (add before public launch).
