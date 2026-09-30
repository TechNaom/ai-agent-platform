# ADR-0006: Public code, private content vault

- Status: Accepted · 2026-09-30

## Context
This repo is public (portfolio). Drafts, unpublished posts, analytics, backups and the
repo exclude list are private. The owner requires everything valuable to live in
GitHub, not only on a local machine.

## Decision
A private repo **`TechNaom/technaom-content-vault`** holds generated content exports,
carousel assets, nightly database backups and private config (such as the repo exclude
list). The engine writes to it with a scoped token. Code, docs and eval harnesses stay
in this public repo.

## Consequences
Nothing private leaks via the public repo, and nothing valuable exists only locally.
