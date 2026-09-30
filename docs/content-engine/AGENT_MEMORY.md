# Agent Memory Design

Status: **Accepted** (Sprint 0, 2026-09-30). See ADR-0002.

## The core idea

**Agents are stateless. Memory lives outside them.**

An LLM remembers nothing between calls. Each agent call starts blank and "remembers"
only what we put into its context window for that call. So agent memory is two things:

1. **Where knowledge is stored** (durable, shared, in Postgres).
2. **How the right slice is loaded** into each agent's prompt at the right time (the
   *context builder*, which is context engineering).

We do **not** give each agent a private memory. The PRD (§34) is explicit: independent
agents with separate state produce duplicate posts, conflicting schedules and lost
history. There is **one memory**, and every agent reads and writes it through typed functions.

## Six memory layers

| # | Layer | What it holds | Stored in | Lifetime | Used by |
|---|---|---|---|---|---|
| 1 | **Working memory** | The prompt for this single call: task, retrieved facts, examples, rules | The context window | One call | Every agent |
| 2 | **Shared state** | Content inventory, lifecycle status, schedule slots, publications, job queue | Postgres tables | Permanent | All agents + orchestrator |
| 3 | **Semantic memory** | Embeddings of source chunks, published posts, news events. It answers "what do my repos say about X?" and "have I already said this?" | Postgres + **pgvector** | Permanent, re-embedded on change | Mapper, Writer, Dedup, Fact-Checker |
| 4 | **Episodic memory** | What happened: every run, draft, rejection reason, fact-check failure, metric, trace ID | Postgres `runs`, `drafts`, `quality_reports`, `claims`, `metrics_snapshots` + Langfuse | Permanent | Analyst, Strategist, debugging |
| 5 | **Procedural memory (learned)** | Distilled lessons: "number-led hooks outperform questions for architecture posts", "source X failed fact-check 3 times" | Postgres `lessons` table, **versioned** | Until retired | Writer, Strategist, News Analyst |
| 6 | **Identity memory (brand)** | Positioning, 5 brand pillars, voice style guide, banned phrases, authenticity rules | Versioned files in git (`content_engine/voice/`) | Changes only via PR | Writer, Judge, Channel Adapter |

## How an agent gets its memory: the context builder

Each agent has a **context recipe**: a function that assembles its prompt from the layers
within a token budget. Nothing is loaded "just in case".

Example: the **Writer** drafting a post from `rag-for-everyone` chapter 17:

```text
Identity (layer 6)       style guide + authenticity rules              ~1.5K tokens
Few-shot (layer 3)       3 of Manohar's own posts most similar in format ~2K
Source facts (layer 3)   top-k chunks from chapter 17, with file paths  ~4K
Avoid list (layers 2+3)  last 20 hooks used + nearest published posts  ~1K
Lessons (layer 5)        top 5 active lessons for this format/pillar     ~0.5K
Task                     the opportunity: angle, format, pillar          ~0.3K
```

Every recipe is plain code: testable, token-budgeted, and logged in the Langfuse trace, so
we can always see exactly what an agent "remembered" when it made a decision.

## How memory is written

- **Agents never write free-form memory.** They return structured output (Pydantic
  models). The orchestrator validates it and writes it through repository functions
  (`save_draft()`, `record_claims()`, `mark_rejected(reason=...)`).
- **Every write is attributable**: agent name, model, prompt version and trace ID.
- **Lessons (layer 5) are gated.** The Engagement Analyst *proposes* lessons weekly. A
  lesson becomes active only if the eval suite shows it doesn't lower quality or
  fact-check scores. This stops the system from "learning" to chase engagement at the
  cost of credibility (PRD §27).
- **Identity (layer 6) changes only through a pull request**, because it's the brand.

## Forgetting and hygiene

- Lessons expire, or are re-validated, after 90 days.
- Knowledge-map nodes whose source file was deleted are archived, not silently kept.
- Semantic memory is re-embedded only for changed files (blob SHA diff).
- Episodic data is kept permanently (it's the audit trail) and backed up nightly to the
  private content vault.

## Why Postgres + pgvector (and not a memory framework)

- **One transactional store** for state and vectors, so dedup ("is this similar to anything
  published?") and scheduling can't disagree.
- **Provider-neutral**: it works the same whether an agent runs on Claude, Grok or Llama
  (ADR-0003). Vendor memory features (for example Claude's memory tool) are tied to one
  provider.
- Mem0 / LangGraph memory would add a dependency without adding a capability we need.
  This matches the framework-light philosophy.

## Tables added for memory (on top of the plan's §5 schema)

```text
lessons          (id, scope[format|pillar|channel|source], statement, evidence, proposed_by,
                  status[proposed|active|retired], eval_run_id, created_at, expires_at)
context_recipes  -- code, not a table: content_engine/memory/recipes.py
prompt_versions  (id, agent, version, hash, created_at)   -- which prompt produced which output
```
