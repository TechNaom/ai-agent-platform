# Security

## Reporting

Please report vulnerabilities privately via GitHub's "Report a vulnerability" (Security
tab) rather than a public issue.

## Controls in this repo

- **Secret scanning + push protection** are enabled on GitHub. CI also runs gitleaks on every PR.
- **Pre-commit gitleaks hook** blocks secrets before they are committed.
- **Dependabot** keeps pip and GitHub Actions dependencies patched.
- **Least privilege:** the content engine reads GitHub with a fine-grained, read-only
  token. Channel tokens (LinkedIn, X, Meta, and so on) have posting scope only.
- **Secret storage:** `.env` locally (git-ignored), GitHub Actions secrets in CI, Fly.io
  secrets in production. Secrets never appear in prompts, logs, traces or the database.
- **Public repo, private content:** drafts, published content, analytics and database
  backups live only in the private content-vault repo and the production database.
- **Publishing safety:** a kill switch, hard daily caps, fact-check and quality gates. The
  default when in doubt is to skip, not publish (see `docs/content-engine/ARCHITECTURE_PLAN.md` §10).
