# Deployment targets (ADR-0008)

The application is one container image plus a PostgreSQL + pgvector database, configured
only by environment variables. Each folder here is an *adapter* for one platform. The
application code never changes per platform.

| Folder | Platform | Status |
|---|---|---|
| `fly/` | Fly.io (compute) + Neon (Postgres) | First target, added with issue #9 |
| `compose/` | Any VM with Docker Compose | Planned |
| `k8s/` | Any Kubernetes (EKS, GKE, AKS, …) | Planned |

Required environment: `DATABASE_URL`, provider API keys, `LANGFUSE_*`, `ENVIRONMENT`.
