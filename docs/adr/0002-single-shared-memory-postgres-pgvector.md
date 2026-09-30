# ADR-0002: Single shared agent memory in Postgres + pgvector

- Status: Accepted · 2026-09-30

## Context
The content engine runs 10 LLM agents. The PRD (§34) warns that agents with independent
state cause duplicate posts, conflicting schedules and lost history. Dedup needs vector
similarity checked in the same transaction as scheduling.

## Decision
All agent memory (shared state, semantic vectors, episodic history, learned lessons)
lives in one Postgres database with pgvector (managed: Neon). Agents are stateless; a
per-agent *context builder* loads the relevant slice into each prompt. Identity/brand
memory is versioned files in git. Full design: `docs/content-engine/AGENT_MEMORY.md`.

## Consequences
- One backup target, one source of truth, transactional dedup.
- No agent-memory framework dependency; the design is provider-neutral.
- ChromaDB remains for the interactive RAG demo agents, which are a separate product.
