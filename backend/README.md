# Backend — FastAPI + Anthropic

See ../docs/ARCHITECTURE.md. Build order in ../PROJECT_STATE.md.

Planned entry point: `app/main.py` (FastAPI app, streaming SSE agent endpoints).
Agent modules live in `app/agents/`, RAG in `app/rag/`, observability in `app/obs/`,
evals in `app/evals/`.
