# Content Engine (multi-channel): Architecture Plan

Status: **PROPOSAL, not approved. No code has been written.**
Date: 2026-09-28
Source: the "Autonomous LinkedIn Content Agent" PRD (39 sections), refined below.

This plan turns the PRD into a buildable design inside `ai-agent-platform`. It keeps the
PRD's intent and fixes the places where a literal build would be fragile, unsafe or
impossible given real LinkedIn API limits. Decisions that need the owner's input are
listed at the end (§14).

---

## 0. Purpose: build the Manohar Papasani brand, AI-centric

The goal is not "post a lot". It is to make **Manohar Papasani** recognizable as a
**GenAI Solution Architect & AI Systems Builder**: a practitioner who builds real AI
systems and teaches them for free. Every design choice below serves that goal.

- **Positioning:** "I build production AI systems (agents, RAG, evals, observability)
  and show exactly how." It's a practitioner's voice, not a news commentator's (PRD §32).
- **Brand pillars** (every post maps to exactly one):
  1. Building real AI systems: agents, RAG, MCP, context engineering
  2. AI engineering in production: evals, observability, security, cost, deployment
  3. AI news through a practitioner lens: what changed and what it means for builders
  4. AI enablement & leadership: teams, workflows, AI-native engineering
  5. Teaching AI: the free "for Everyone" courses as proof of depth
- **AI-centric filter:** a post that doesn't connect to AI doesn't ship. Non-AI repos are
  reframed through an AI lens (devops → LLMOps and AI-assisted DevOps; python → Python
  for AI engineers) or used sparingly.
- **Authenticity rule (brand safety):** a first-person claim ("I built…", "I learned…",
  numbers, outcomes) is allowed only when it's backed by evidence in a repo or an
  existing post. The engine never invents experiences, results or stories.
- **Transparency as a brand asset:** an AI architect whose LinkedIn is run by an
  autonomous agent he built is itself the strongest proof of the positioning. The engine
  becomes a build-in-public series of its own, openly disclosed.
- **Funnel:** posts point to the courses, repos and live sites, so followers turn into
  learners and GitHub stars. Brand metrics (followers, profile views, repo stars,
  course traffic) sit alongside post engagement in the learning loop.
- **Quality over volume:** 2/day is the default, but the editorial engine drops to 1/day
  rather than publish anything below the bar. One weak post costs more brand than one
  missed slot.
- **What the engine can't do:** replying to comments is where brand relationships form.
  The engine posts. Manohar replies, helped by a daily "comments worth answering" digest.

## 1. What we are building (one paragraph)

It's a **stateful, scheduled, multi-agent content system** that runs as the platform's
fifth product, next to the four interactive demo agents. It has two sources: (A) the
owner's GitHub repos, turned into a knowledge map and then into content opportunities,
and (B) a continuously ranked AI-news pool. Both feed one **editorial engine**, which
publishes two posts a day to LinkedIn and lets verified breaking news interrupt the
schedule. Every step is traced in Langfuse and every draft is scored by an eval gate. The
system's one "memory" is a single Postgres database, and nothing publishes unless the
gate passes. The default when in doubt is **skip, don't publish**.

It reuses the platform's spine instead of duplicating it:

| Platform piece (already planned) | How the content engine uses it |
|---|---|
| Provider-abstracted model layer | Sonnet for writing/decomposition/fact-check, Haiku for triage and cheap scoring, OpenRouter/Groq as the cheap fallback |
| Tool Runner agent runtime | The LLM agents (decomposer, writer, fact-checker, judge) |
| Langfuse observability | One trace per pipeline run, with scores attached to every draft |
| Offline eval harness + CI gate | Voice, fact-check, dedup, ranking and decomposition eval sets |
| Guardrails (spend cap) | Daily/monthly LLM budget for the background worker |

### Scale & scope (owner direction, 2026-09-28)

- **Source = the entire TechNaom GitHub account**, auto-discovered, not a hand-picked
  list. New repos are picked up automatically. Only an explicit **exclude list** is kept
  (private client repos, private notes, and test/dogfood copies).
- **Target inventory: 500–1,000+ posts.** Measured corpus (2026-09-28): ~5,300
  md/html/ipynb/py files across 28 repos. The 10 "for Everyone" course repos alone hold
  ~4,800 (devops 1,353 · genai 798 · rag 692 · python 577 · ai-engineering 265 ·
  llm-evaluation 260 · ai-security 245 · context-engineering 242 · ai-coding-agents 201 ·
  mcp 161), plus enterprise-knowledge-assistant, agentic-ai, git-actually, ai-agent-platform.
- **Two output formats: text posts AND carousels** (LinkedIn PDF document posts), both
  generated, rendered, validated and published with no manual step (§4.3).
- **Fully automated end to end:** discover → decompose → write → design carousel →
  validate → schedule → publish → measure.
- The 48 posts in `linkedin-posts` are **not the content source**. They are used only as
  the voice/style sample and as the "already published" history for dedup.

**Implication: plan the whole inventory, draft just in time.** At 2 posts/day, 1,000
posts is ~16 months of runway. The engine therefore builds the **full opportunity
inventory up front** (all repos → knowledge map → 1,000+ ranked opportunities with
evidence, cheap to store) but writes and renders final posts only **~7–10 days ahead**.
Drafts stay fresh, benefit from the learning loop, and a repo change never leaves
hundreds of stale drafts behind. The inventory also gives a **series plan** per repo
(e.g. "DevOps for Everyone, Day X/N") so posts come out as coherent arcs, interleaved
across repos per the mix rules, rather than as random picks.

Existing assets to **absorb, not rebuild**:

- `TechNaom/linkedin-news-agent`: the Tavily client, LinkedIn client, critique gate and
  `check_token_expiry.py` get ported in, and that repo is retired once parity is reached.
- `linkedin-posts`: 48 real posts. They become (1) the **voice corpus** (style guide,
  few-shot examples, brand-consistency eval set) and (2) the **seed publication history**,
  so the engine never re-posts RAG-for-Everyone Days 1–30 or posts 01–45.

---

## 2. Refinements to the PRD (where this plan deliberately differs)

1. **Fully automated end state, reached through a short automatic burn-in.** The owner
   wants zero manual steps. The burn-in adds none: SHADOW just means "publish to a
   digest instead of to LinkedIn" while the gates prove themselves. The same pipeline runs in three
   modes, controlled by one config switch:
   `SHADOW` (generates and schedules, never publishes; the owner reviews the daily output) →
   `VETO` (auto-publishes unless the owner vetoes within a window, e.g. 2 h) →
   `AUTONOMOUS` (the PRD target). Promotion happens only when measured criteria are met
   (§11). This is how the PRD's "no human in the loop" is reached safely rather than assumed.
2. **The orchestrator is a deterministic state machine, not an LLM agent.** Scheduling,
   queueing, cooldowns, caps and lifecycle transitions are code: testable and predictable.
   LLMs are used only where judgment is needed (understanding, ranking, writing,
   checking). Of the PRD's ~12 "agents", 5 are LLM agents and the rest are services (§4).
3. **Hard caps above the priority model.** Normal is 2 posts/day, with an absolute max of
   3/day. Breaking news can take one extra slot per day at most and needs **≥2 independent
   credible sources, or the primary announcement**. This prevents a busy news day from
   turning the account into a feed.
4. **The analytics loop must work with partial data.** Metrics for personal-profile posts
   may be unavailable or restricted in LinkedIn's API (verified in the Phase 0 spike).
   The learning engine is designed to run on whatever exists: API metrics, a manual CSV
   export import, or none. It never blocks publishing.
5. **One unavoidable human touchpoint.** LinkedIn personal-app access tokens expire about
   every 60 days with no programmatic refresh. The engine warns 7 days ahead (ported
   from `linkedin-news-agent`) and falls back to SHADOW automatically on expiry. It
   never fails silently.
6. **News posts link their sources and never reproduce article text.** They summarize,
   interpret and link (in the post or the first comment, a configurable choice).
   Claims are tagged as confirmed, announced, reported or speculation, per PRD §16.
7. **Learning optimizes inside a quality floor.** Engagement signals re-weight format,
   topic and time choices. They never lower the quality or fact-check thresholds (PRD §27
   "don't chase engagement", made enforceable).

---

## 3. System context

```text
 ┌─────────────── GitHub (owner's repos) ───────────────┐     ┌──── News sources ────┐
 │ READMEs, chapters, docs, code, commits (via gh API)  │     │ RSS / vendor blogs,  │
 └───────────────────────────┬──────────────────────────┘     │ arXiv, Tavily/web    │
                             │                                └──────────┬───────────┘
                             ▼                                           ▼
 ┌──────────────────────── Content Engine worker (Fly.io) ──────────────────────────┐
 │  Scheduler (APScheduler) → durable job table → pipelines (idempotent jobs)       │
 │                                                                                  │
 │   GitHub Engine ──┐                                   ┌── News Engine            │
 │                   ▼                                   ▼                          │
 │              Quality Gate (dedup + fact-check + judge rubric)                    │
 │                               ▼                                                  │
 │                     Editorial Engine (rules + priority)                          │
 │                               ▼                                                  │
 │                    Publisher (outbox, idempotent) ───────────────► LinkedIn API  │
 │                               ▼                                                  │
 │                   Analytics collector → Learning weights                         │
 └───────────────┬──────────────────────────────┬───────────────────────────────────┘
                 ▼                              ▼
     Postgres + pgvector (the memory)    Langfuse (traces, scores, cost)
                 ▲
     Owner dashboard (auth-gated) + GitHub-Issue alerts / daily digest
```

---

## 4. Components

### 4.1 Services (deterministic code)

| Service | Responsibility |
|---|---|
| **Scheduler / Orchestrator** | Cron triggers → enqueue jobs into a Postgres job table (`SELECT … FOR UPDATE SKIP LOCKED`). Retries with backoff, dead-letter, per-source circuit breakers (PRD §23: one source down ≠ system down). No Redis/Celery. |
| **Repo Scanner** | Lists configured repos, walks trees, and stores files with their **blob SHA**. Change detection = SHA diff since `last_scanned_commit`, so only new or modified content is reprocessed (PRD §25). |
| **News Collectors** | RSS/Atom feeds from an allow-listed source registry (vendor blogs, arXiv, trusted press) for the bulk 50–100 candidates. Tavily or Claude `web_search` is used for **verification and corroboration**, not bulk collection (this keeps Tavily inside its free tier). |
| **Dedup Service** | 4 layers: exact hash → normalized-text hash → embedding similarity (pgvector) against published and queued posts → news-event clustering (the same story from N outlets is 1 event). Also enforces hook/format repetition limits. |
| **Editorial Engine** | Maintains the queues (GitHub, News, Breaking, Reserved) and fills daily slots using hard rules first (caps, cooldowns, mix targets, PRD §30 rules 1–7), then the priority score (§6). |
| **Publisher** | Outbox pattern: a slot → `publication` row with an idempotency key → LinkedIn Posts API → store the URN/URL. It can never double-post on retry. Handles token expiry, kill switch and mode (SHADOW/VETO/AUTONOMOUS). |
| **Analytics Collector** | Pulls whatever metrics the API allows at T+24h and T+7d, or ingests a CSV export. |
| **Learning Engine** | Thompson-sampling-style weights over {format, hook type, topic cluster, time slot}, bounded by the quality floor. Weekly gap report on inventory and mix. |

### 4.2 LLM agents (Tool Runner, traced)

| Agent | Model | Input → Output |
|---|---|---|
| **Knowledge Mapper / Decomposer** | Sonnet | repo files → knowledge map (chapters → concepts) → *content opportunities*, each with angle, format, audience and evidence pointers back to the source files. Opportunity count follows material richness, with no fixed multiplier (PRD §6). It must cite source spans, and anything uncited is dropped (this is the guard against padding). |
| **News Analyst** | Haiku triage → Sonnet on the top ~15 | candidates → scores (relevance, novelty, impact, significance, engagement, credibility, practical value) + tier `NORMAL / IMPORTANT / HIGH / BREAKING` + extracted facts with a claim-type tag |
| **Post Writer** | Sonnet | opportunity or news brief + **voice pack** (style guide distilled from the 48 posts, retrieved few-shot examples, a banned-phrase list, the recent-hooks list) → draft. Variants: GitHub-practitioner and news-analysis. |
| **Fact-Checker** | Sonnet + web_search | draft → claim ledger (each claim → supporting evidence URL/span or source-file span, status: supported / unsupported / speculation-labelled). Any unsupported factual claim fails the draft. |
| **Quality Judge** | Sonnet (calibrated) | draft → rubric scores for PRD §22 (accuracy, originality, technical correctness, readability, hook, value, brand, CTA, spam-feel, repetition) plus pass/fail with reasons. |

### 4.3 Carousel pipeline (fully automated)

LinkedIn carousels are **PDF document posts**. Each carousel goes through these steps:

```text
opportunity (format = carousel)
   → Carousel Planner (Sonnet): slide spec JSON (8–12 slides: hook, problem, steps/diagram, takeaway, CTA)
   → Diagram step: Mermaid/SVG from spec (architecture, flows, comparisons)
   → Renderer: branded HTML templates → Playwright (headless Chromium) → PDF + PNG previews
   → Visual QA (Sonnet vision on the PNGs): text overflow, contrast, legibility on mobile,
     slide count, spelling, and no code block too small to read → auto-fix loop max 2 rounds
   → Fact-check + judge (same gate as text posts; they judge the slide text + caption)
   → Publisher: LinkedIn Documents API upload → post with caption
```

- The **design system** comes from the existing carousels in `linkedin-posts/carousels/`:
  one template set with fixed brand colors, fonts and layout. It is versioned, so posts
  look consistent without anyone designing by hand.
- Which items become carousels is decided by the editorial engine. The default is ~30% of
  GitHub-derived posts (architecture, step-by-step, comparisons, "N mistakes"), and
  carousels are rarely used for breaking news, where speed matters.
- If carousel upload fails, the fallback is to publish as a text post with a single image,
  or to skip. The slot is never left broken.
- The Phase 0 spike must confirm that document posts via API work for a **personal
  profile** with the `w_member_social` scope.

### 4.4 Agent roster (final, multi-agent)

The orchestrator stays deterministic code (§2.2). It coordinates **10 LLM agents**, and
they share state only through the database (PRD §34):

| # | Agent | Model | Job |
|---|---|---|---|
| 1 | **Repo Knowledge Mapper** | Sonnet | Whole GitHub account → knowledge map with evidence spans |
| 2 | **Content Strategist** | Sonnet | Maps opportunities to brand pillars, builds series arcs per repo, keeps the AI-centric filter |
| 3 | **News Scout & Analyst** | Haiku → Sonnet | Triage, ranking, tiering, corroboration |
| 4 | **Writer** | Sonnet | Canonical post in Manohar's voice |
| 5 | **Carousel Designer** | Sonnet | Slide spec + diagrams → rendered PDF/PNGs |
| 6 | **Channel Adapter** | Sonnet/Haiku | Turns one canonical item into native variants per channel (§4.5) |
| 7 | **Fact-Checker** | Sonnet + web_search | Claim ledger; blocks unsupported claims |
| 8 | **Brand & Quality Judge** | Sonnet | Rubric + authenticity rule + AI-centric check, per variant |
| 9 | **Visual QA** | Sonnet vision | Layout/legibility checks on every rendered asset |
| 10 | **Engagement Analyst** | Haiku | Per-channel metrics → learning weights; daily "comments worth answering" digest |

### 4.5 Multi-channel distribution: create once, adapt natively, publish everywhere

```text
canonical item (post + optional carousel + source links)
   → Channel Adapter agent → one variant per enabled channel
       (length, tone, hashtags, links, media format, thread splitting)
   → per-variant gate (judge + fact-check reuse; similarity check per channel)
   → per-channel schedule (own times + own daily cap)
   → Channel Publisher plugin (common interface) → outbox row per (item, channel)
   → per-channel metrics → Engagement Analyst
```

Every channel is a **plugin** implementing
`capabilities()` (max length, media types, threads, documents, rate limits),
`adapt_hints()`, `publish(variant)`, `delete(ref)`, `fetch_metrics(ref)`.
One channel failing never blocks the others (outbox per channel, circuit breaker per channel).
Adding a channel means adding a plugin plus a config entry. The core doesn't change.

**Channel reality check.** Everything here is to be verified in the Phase 0 spike;
API access and pricing on these platforms change often.

| Channel | How it publishes | Carousel becomes | Known constraints | Brand value |
|---|---|---|---|---|
| **LinkedIn** (primary) | Posts API, `w_member_social`, personal profile | Native PDF document post | 60-day token, no refresh; metrics may be restricted | ★★★ core professional audience |
| **X (Twitter)** | API v2 create post | Thread with up to 4 images/post | Paid API access (verify current tier/pricing); 280 chars unless Premium | ★★ AI builder community |
| **Facebook** | Graph API **Page** posts only (API can't post to personal profiles) | Multi-photo post | Needs a "Manohar Papasani" Page + Meta app review (`pages_manage_posts`) | ★ |
| **Instagram** *(added)* | Graph API content publishing (professional account) | **Native carousel**, a great fit | Same Meta app review; image-first | ★★ reach for carousels |
| **Threads** *(added)* | Threads API publishing | Carousel supported | Meta app | ★ |
| **WhatsApp** | **Cloud API broadcast to opted-in subscribers** (a daily/weekly AI digest). The API can't post to Status or to WhatsApp Channels | Link + cover image | Meta Business verification, approved message templates, **paid per marketing message**, opt-in required by policy | ★★ direct line to learners |
| **Slack** | Incoming webhook / `chat.postMessage` to a community or learner workspace | Link + images | Easy, free | ★ community |
| **Telegram** *(added)* | Bot API → public channel | Media group (album) | Easy, free | ★ learner community |
| **Discord** *(added)* | Webhook → announcements channel | Images | Easy, free | ★ |
| **Bluesky** *(added)* | AT Protocol API | Up to 4 images/post | Easy, free | ★ growing AI/dev crowd |
| **Own blog: TechNaom site on GitHub Pages** *(added, recommended)* | Git commit of an expanded long-form article | Embedded slides | Free, **owned audience + SEO**, canonical home that other posts link back to | ★★★ |
| **Dev.to / Hashnode** *(added)* | Official APIs, cross-post of blog articles with canonical URL | Embedded | Free | ★★ developer discovery |
| **Newsletter** *(optional)* | Buttondown/beehiiv API weekly digest | Links | LinkedIn/Substack newsletters have no posting API | ★★ owned audience |
| Not automatable | YouTube Community, LinkedIn Newsletter, Medium (API closed to new integrations) | | | |

**Per-channel cadence (defaults):** LinkedIn 2/day · X 2–4/day (threads + news) ·
Instagram/Threads/Facebook 1/day (carousel-first) · Bluesky mirrors X ·
Slack/Telegram/Discord 1/day · WhatsApp **one digest per week** (paid, and
over-messaging causes opt-outs) · Blog/Dev.to 1–2 long-form/week (the best GitHub
chapters, expanded).

On failure: a failed draft gets **one** regeneration from a different angle (PRD §30 rule 7).
If that also fails, it is `REJECTED` and logged with the reasons. Nothing is forced.

---

## 5. Data model (Postgres + pgvector)

This refines PRD §28, adding what's needed for dedup, fact-check audit, scheduling
safety and observability.

```text
sources            (id, kind[github|news_feed], name, url, config, credibility, status, last_scanned_at, last_commit_sha)
source_documents   (id, source_id, path, blob_sha, title, content, embedding, updated_at)
knowledge_nodes    (id, source_id, parent_id, kind[repo|chapter|concept], title, summary, doc_refs[])
opportunities      (id, knowledge_node_id?, news_event_id?, angle, format, content_type, audience,
                    evidence_refs[], priority, status, created_at)
news_items         (id, url, source_id, headline, published_at, raw_excerpt, hash, embedding, event_id)
news_events        (id, title, tier, scores{...}, corroboration_count, primary_url, first_seen, status)
drafts             (id, opportunity_id, version, body, hook_type, format, length, embedding,
                    langfuse_trace_id, status, created_at)
claims             (id, draft_id, text, claim_type[confirmed|announced|reported|speculation],
                    evidence_url, evidence_span, verdict)
quality_reports    (id, draft_id, rubric{...}, overall, passed, reasons, judge_model)
schedule_slots     (id, date, slot[morning|evening|breaking], draft_id, state, replaced_draft_id)
publications       (id, slot_id, draft_id, idempotency_key UNIQUE, linkedin_urn, url, mode,
                    published_at, error)
metrics_snapshots  (id, publication_id, taken_at, impressions, reactions, comments, shares, saves, source[api|csv])
topic_history      (topic_key, last_published_at, cooldown_until, count)
jobs               (id, type, payload, state, attempts, run_after, last_error)   -- durable job queue
runs               (id, pipeline, started_at, finished_at, status, cost_usd, langfuse_trace_id)
settings           (key, value)  -- mode, kill_switch, mix targets, caps, cooldowns, slot times
```

**Content lifecycle** (PRD §26), enforced as a state machine on `opportunities`, `drafts` and `schedule_slots`:
`DISCOVERED → ANALYZED → DECOMPOSED → GENERATED → VALIDATED → QUEUED → SCHEDULED → PUBLISHED → MEASURED → ARCHIVED | RECYCLABLE`, plus the terminal `REJECTED` and `SKIPPED` (with a reason).

---

## 6. Editorial logic

**Order of evaluation, every planning run:**

1. **Hard gates:** kill switch, mode, token validity, daily cap (2 normal / 3 absolute),
   topic cooldown (evergreen ~30 days, news event 0 days if there's a material update),
   format/hook repetition window.
2. **Breaking path:** a `BREAKING` event with ≥2 credible sources or the primary
   announcement → generate now → gate → publish in the next practical window (with at
   least ~3 h between posts). At most one breaking slot per day.
3. **Slot fill:** morning prefers GitHub/educational, evening prefers news/architecture
   (PRD §18). The best candidate comes from the priority score
   `P = w·[relevance, importance, freshness, originality, practical_value, engagement_potential, practitioner_bonus]`,
   where the **practitioner bonus** encodes PRD §32 (the owner's own implementation work
   beats generic commentary).
4. **Mix correction:** a rolling 14-day mix vs the targets (40/25/15/10/10, configurable)
   nudges the weights.
5. **Starvation rules:** if the news quality is low, don't fill the slot with news; use
   GitHub content (§30 rule 5). If the queue has more than ~21 days of runway, pause
   generation (rule 6). If it has less than ~5 days, raise the generation budget.

---

## 7. Background cadence (PRD §24)

| Job | Cadence |
|---|---|
| News collect + triage | every 3 h |
| Breaking-news check (tier re-score on new corroboration) | hourly (cheap, Haiku) |
| Draft generation to keep ~7–10 days of runway | daily 02:00 IST |
| Plan the next 48 h of slots | daily 03:00 IST + after any breaking event |
| Publish | slot times (default 08:30 and 18:30 IST, configurable) |
| GitHub change scan | every 6 h |
| Metrics pull | T+24 h, T+7 d per post |
| Inventory/gap + learning re-weight + owner digest | weekly |
| Token expiry check | daily |

---

## 8. Observability (in Langfuse and the DB)

- **Traces:** one per pipeline run (scan, news cycle, generation, planning, publish), with
  nested spans per agent and tool call, plus token cost and latency.
- **Scores on every draft:** rubric scores, fact-check pass rate, max similarity to history.
- **Health signals:** queue runway (days), gate pass rate, skip reasons, source failure
  rate, publish success, cost/day vs budget, days to token expiry.
- **Alerts:** a GitHub Issue plus an email-style digest (the pattern `linkedin-news-agent`
  already uses) for publish failures, token expiry in 7 days or less, runway under 3 days,
  budget over 80%, and repeated fact-check failures on a source.

## 9. Evaluation

| Eval set | Built from | Metric / gate |
|---|---|---|
| **Brand voice** | the 48 real posts vs generic LLM posts | judge agreement / pairwise-preference accuracy |
| **Fact-check** | real drafts with **seeded false claims** | catch rate ≥ 95% (CI gate) |
| **Dedup** | labelled near-duplicate / distinct post pairs, incl. the RAG-30 series | precision/recall on "duplicate" |
| **News ranking** | ~100 historical stories labelled by the owner | NDCG@10, breaking-tier precision |
| **Decomposition** | 3–4 repos (e.g. rag-for-everyone, python-for-everyone) | coverage of chapters, % opportunities with valid evidence, owner-rated usefulness |
| **Judge calibration** | owner's publish/no-publish labels during SHADOW | agreement with the owner (the gate must match the owner's taste before autonomy) |

Offline sets run in CI and block merges on regression. Online, every production draft is scored in Langfuse.

## 10. Safety & reliability controls (PRD §36)

- **Kill switch** (a settings flag plus a CLI/dashboard toggle). It is checked immediately before every publish call.
- **Refuse to publish** when: fact-check has any unsupported claim, sources are
  uncorroborated for news, similarity to history is above the threshold, or the judge fails.
  **Skipped slots are acceptable.**
- **Idempotent publishing, audit log of every publish, and a one-command delete of a published post.**
- **Content policy:** no private individuals named, no unverifiable statistics, no
  reproduced article text, and speculation always labelled.
- **Budget guard:** a daily LLM spend cap for the worker. When it's exceeded, the worker
  degrades to cheap models or pauses generation. It never pauses publishing of already-approved drafts.
- **Secrets:** LinkedIn/GitHub/Anthropic keys live only in Fly secrets. The repo is public,
  so **no drafts, DB dumps or tokens are ever committed**.

## 11. Autonomy rollout criteria

| Promote | Requires |
|---|---|
| SHADOW → VETO | ≥14 days of shadow output; owner would have published ≥85% of drafts; 0 factual errors found in review; fact-check eval ≥95% |
| VETO → AUTONOMOUS | ≥14 days in VETO with ≤1 veto/week, no publish incidents, all health alerts green |

Any factual error found in production drops the system back to VETO automatically.

---

## 12. Code layout (inside `ai-agent-platform`)

```text
backend/app/
  core/            # shared kernel (model layer, config, tracing), built first, used by all 5 products
  agents/          # the 4 interactive demo agents (existing plan)
  content_engine/
    sources/       # github_scanner.py, news_collectors.py, source_registry.yaml
    agents/        # decomposer.py, news_analyst.py, writer.py, fact_checker.py, judge.py
    voice/         # style_guide.md, few-shot selection, banned phrases
    editorial/     # rules.py, priority.py, planner.py
    publish/       # linkedin.py (ported), outbox.py, token_watch.py (ported)
    learning/      # analytics.py, weights.py
    store/         # SQLAlchemy models + Alembic migrations
    worker.py      # scheduler entrypoint (separate Fly process group)
  evals/content_engine/   # the 6 eval sets + runners
frontend/ …/content       # owner dashboard (auth-gated, never on the public demo nav)
```

---

## 13. Build phases (re-sequenced from PRD §37 with gates)

| Phase | Scope | Exit criterion |
|---|---|---|
| **0: Spikes (1–2 days)** | Verify LinkedIn Posts API + scopes + what member analytics are actually available; confirm the news source list; import the 48 posts; cost model | Written findings; the plan updated if the API differs |
| **1: Foundation** | Platform kernel (model layer, Langfuse, config) shared with the 4 agents; Postgres schema + migrations; job queue + worker; GitHub scanner with SHA change detection | Scan 3 repos incrementally; traces visible |
| **2: GitHub content engine** | Account-wide discovery + exclude list, knowledge map for all repos, full opportunity inventory + series plans, voice pack, writer, dedup, judge, fact-check (source-grounded) + evals | **500+ evidence-backed opportunities** across the account with none duplicating already-published posts; **SHADOW starts** (a daily digest of what would be posted) |
| **2b: Carousel pipeline** | Slide-spec planner, diagram step, branded templates, Playwright render, vision QA loop | 20 carousels auto-generated with 0 layout defects on vision QA + owner spot-check |
| **3: News engine** | Collectors, clustering, ranking/tiers, corroboration, news writer, claim ledger + ranking/fact-check evals | Top-10 daily list the owner agrees with; seeded-claim catch ≥95% |
| **4: Editorial engine** | Queues, priority, mix, cooldowns, breaking override, caps, planner | 14 simulated days produce a valid schedule with 0 rule violations |
| **5: Publishing, wave 1** | Channel plugin interface + Channel Adapter agent; LinkedIn (outbox), own blog, Slack, Telegram, Discord; token watch, kill switch, owner dashboard | First real posts across wave-1 channels |
| **5b: Wave 2** | X, Bluesky, Dev.to/Hashnode | Threads/cross-posts live |
| **5c: Wave 3** | Facebook Page, Instagram, Threads (after Meta app review, which can take weeks, so start the application in Phase 0) | Carousels live on Meta channels |
| **5d: Wave 4** | WhatsApp digest (after Business verification + template approval + opt-in page) | Weekly digest to subscribers |
| **6: Learning loop** | Metrics (API/CSV), learning weights, weekly reports | Weights update without lowering quality scores |

Crash-safety: every meaningful chunk is committed and pushed (existing repo mandate).
Build sessions run on Sonnet.

**Rough running cost (estimate, to be measured in Phase 0):** about 8 news cycles/day of
Haiku triage, ~15 Sonnet analyses, 3–5 drafts plus a fact-check and judge per draft ≈
**$1–3/day on Claude** (~$30–90/month). Infra: Fly worker plus a small Postgres (Neon
free tier or Fly) ≈ $0–10/month. Tavily stays in its free tier because bulk collection is RSS.

---

## 14. Decisions needed from the owner before build

1. **Placement:** build as a module inside `ai-agent-platform` (recommended: it shares
   the kernel, evals and observability, and becomes the platform's "real production
   workload" story) or as a separate repo that imports the platform?
2. **Priority vs the existing roadmap:** build the content engine **first** (it forces the
   shared kernel into existence, and the 4 demo agents follow), or after the 4 demo agents?
3. **Autonomy rollout:** accept SHADOW → VETO → AUTONOMOUS with the §11 criteria, or go
   straight to AUTONOMOUS?
4. **Exclude list** (the whole account is ingested by default). Proposed: exclude all
   private client repos, private idea notes, and test/dogfood copies (the exact list is
   kept in private config, not in this public doc).
8. **Channels:** approve the waves in §13, and create the accounts that don't exist yet
   (Facebook Page, Instagram professional account, X API access, Bluesky, Telegram
   channel, Slack/Discord community).
5. **Budget:** a monthly LLM cap for the worker (suggested $75) and hosting (Fly + Neon).
6. **Post timing (IST) and link placement** for news sources (in the post vs the first comment).
7. **Retire `linkedin-news-agent`** once the news engine reaches parity?
