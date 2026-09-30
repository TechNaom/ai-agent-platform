# Contributing

This repo is run like a production engineering team's repo. The same rules apply to
humans and to AI coding assistants.

## Workflow

1. **Every change starts as a GitHub issue** (feature or bug template) inside a milestone
   (sprint / phase).
2. **Branch from `main`**: `<type>/<issue-number>-<short-slug>`, e.g. `feat/12-github-scanner`.
   Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`.
3. **Commit early, push often.** Nothing valuable lives only on a local machine.
   Commit messages follow Conventional Commits: `feat(content-engine): add repo scanner`.
4. **Open a pull request** using the template and link the issue (`Closes #12`).
5. **CI must pass**: lint, format, type check, tests, secrets scan and (once they exist)
   evals. `main` is protected, so there are no direct pushes and no merging on red.
6. **Squash-merge.** The PR title becomes the commit on `main`. No approving review is
   required: AI assistants may merge their own PRs once CI is green (owner authorization,
   2026-09-30). The exceptions need the owner first: going live with publishing (or
   promoting SHADOW → VETO → AUTONOMOUS), anything that spends money, irreversible
   operations, and secrets.
7. **Architectural decisions get an ADR** in `docs/adr/`.
8. **Keep `PROJECT_STATE.md` and `AI_HANDOFF.md` current** at the end of each work session.

## Local setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install          # ruff, gitleaks, yaml checks on every commit
ruff check . && ruff format --check . && mypy && pytest
```

## Secrets

Never commit secrets and never paste them into chats or issues. Local development uses
`.env` (git-ignored). CI uses GitHub Actions secrets, and production uses Fly.io secrets.
See `SECURITY.md`.

## Content

Generated drafts, published posts, carousels and database backups belong in the
**private** `TechNaom/technaom-content-vault` repo, never in this public repo.
