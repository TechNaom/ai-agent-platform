# ADR-0008: Platform-agnostic deployment, no local infrastructure

- Status: Accepted · 2026-09-30
- Amends ADR-0004: Fly.io + Neon become the *first deployment target*, not a dependency.

## Context
The owner requires (1) **nothing running on their own machine** (no local databases,
containers or services) and (2) a **platform-agnostic** solution with no lock-in to one
cloud vendor.

## Decision

**Portable by construction:**

| Concern | Portable choice | Runs on |
|---|---|---|
| Compute | One OCI container image (`api` + `worker` entrypoints) | Fly.io, Render, Railway, AWS (ECS/App Runner), GCP Cloud Run, Azure Container Apps, any Kubernetes, any VM with Docker |
| Database | Plain **PostgreSQL 16+ with pgvector**, reached only via `DATABASE_URL` | Neon, Supabase, AWS RDS/Aurora, GCP Cloud SQL, Azure Flexible Server, self-hosted |
| Scheduling | In-app, DB-backed (ADR-0004); **no** EventBridge / Cloud Scheduler dependency | Anywhere the container runs |
| Secrets & config | Environment variables (12-factor) | Any platform's secret manager |
| Observability | Langfuse (open source: cloud or self-hosted) + standard JSON logs | Anywhere |
| LLMs | Provider-neutral router (ADR-0003) | Any provider |

**Rules:**
- The core code (`backend/app/`) imports **no cloud-vendor SDK**. Platform specifics live
  only in `deploy/<target>/` (manifests, deploy workflow). Switching platform means adding
  a folder, not changing code.
- First target: **Fly.io (compute) + Neon (Postgres)**, chosen on cost and simplicity only.

**Nothing local:**
- **Tests** run in GitHub Actions, with Postgres + pgvector as a CI *service container*
  on GitHub's machines.
- **Development** runs in **GitHub Codespaces** (`.devcontainer/`, Postgres included)
  when a human wants a live environment, in the browser or in VS Code remote.
- **Staging and production** run on the chosen cloud target.
- The only local artefact is the git working copy the coding assistant edits. It's
  backed up to GitHub on every push, and it can itself move to a cloud session.

## Consequences
- No vendor lock-in; migration is a config and manifest change.
- No local Docker, databases or services are required for any workflow.
- We give up vendor-native conveniences (for example managed cron), which the in-app
  scheduler already covers.
