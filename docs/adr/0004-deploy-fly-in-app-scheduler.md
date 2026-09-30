# ADR-0004: Deploy on Fly.io with an in-app, DB-backed scheduler

- Status: Accepted · 2026-09-30

## Context
Publishing is time-sensitive and the schedule is dynamic (breaking news, slot
replacement, per-channel times, retries). GitHub Actions cron can start late or skip
under load, and pauses after 60 days of repo inactivity. A laptop can crash or sleep.

## Decision
- One Docker image on **Fly.io**, two process groups: `api` (FastAPI: dashboard,
  health checks, kill switch) and `worker` (scheduler + agents + publishers).
- Schedules are **rows in Postgres**. The worker ticks every minute and claims due jobs
  with `SELECT … FOR UPDATE SKIP LOCKED`. Jobs are idempotent and retried with backoff,
  with a dead-letter state.
- **GitHub Actions is the watchdog**: an hourly health check that opens an alert issue
  and triggers catch-up if the worker missed a slot. It also runs the nightly backup to
  the private content vault.
- Managed services: Neon (Postgres + pgvector), Langfuse Cloud, GitHub Pages (frontend).

## Consequences
- Precise, restart-safe scheduling. Breaking news inserts jobs instantly.
- A standard container means it can move to AWS (ECS/Lambda + EventBridge) or GCP
  (Cloud Run + Cloud Scheduler) later without a rewrite.
- Estimated $5–15/month for Fly (to be confirmed at first deploy).
