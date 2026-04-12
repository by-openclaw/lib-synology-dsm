# AGENTS.md -- lib-synology-dsm

> **Rules:** [OPERATING-STANDARD.md](https://github.com/by-openclaw/doc-platform-core/blob/main/OPERATING-STANDARD.md) is mandatory for all agents, all sessions. [SOUL.md](https://github.com/by-openclaw/doc-platform-core/blob/main/SOUL.md) · [USER.md](https://github.com/by-openclaw/doc-platform-core/blob/main/USER.md)

Python library for Synology DSM API -- session auth, user/group/share/NFS CRUD, FileStation file ops, quota, bandwidth, traffic control, and storage management.

## Always Read First

Before touching anything in this repo:

1. [`README.md`](README.md) -- library overview, usage, design decisions
2. [`CLAUDE.md`](CLAUDE.md) -- agent-specific constraints, known blockers, API quirks
3. [`docs/feature-coverage.md`](docs/feature-coverage.md) -- primary reference for implemented vs planned features
4. [`docs/api-versions.md`](docs/api-versions.md) -- tested API version table (ground truth)
5. [`docs/api-reference.md`](docs/api-reference.md) -- method reference with confirmed working signatures
6. [`src/synology_dsm/`](src/synology_dsm/) -- library source
7. [`docs/refactor-clarification-2026-03-30.md`](docs/refactor-clarification-2026-03-30.md) -- confirmed decisions and v1.0 priority matrix

## Current Milestone -- v1.0

Target: stable public API, mypy clean, consistent return dicts across all managers.
v1.0 blockers: see CLAUDE.md v1.0 Blockers section and docs/refactor-clarification-2026-03-30.md section 5.

## Coding & Commit Standards

- **Python style:** PEP 8, type hints on all public methods
- **Version:** `pyproject.toml` -- bump with `feat` or `fix` commits per semver
- **Branch naming:** `feat/{issue-id}-{description}` or `fix/{issue-id}-{description}`
- **All new managers** must implement `ensure(state=present|absent)` idempotent pattern
- **No httpx** -- ADR-0001 decision: zero runtime deps -- not a host availability constraint

## What NOT To Do

> Also read `CLAUDE.md` HARD RULES -- architectural decisions enforced there. AGENTS.md and CLAUDE.md are both authoritative. When in doubt, CLAUDE.md wins.

- Do NOT run live integration tests without first checking the DSM blocker below
- Do NOT publish to PyPI without explicit instruction from @yboujraf

## Known Blocker

**DSM account requirements for integration tests:**

Admin account (`API_USER` / e.g. `rune-api`):
- Group: `administrators`
- Applications: DSM = **Allow**, File Station = **Allow**

Audit account (`AUDIT_USER` / e.g. `rune-audit`):
- Group: `users` (no admin rights)
- Applications: DSM = **Allow**, File Station = **Allow** (needed for section 7 FileStation list tests)
- Note: error 402 on login = account disabled in DSM Control Panel -> User & Group -> Edit -> Enable

## GitHub Repo

<https://github.com/by-openclaw/lib-synology-dsm>

## Agent: Rune

Maintained by Rune (DevOps familiar) for the BY-SYSTEMS PoC platform.
Owner: @yboujraf

---

## Project Stats

> Auto-updated on every release. Last updated: 2026-03-31

| Metric | Value |
|---|---|
| Version | v0.10.3 |
| Tagged releases | 12 |
| Unit tests | 345 passing, 100% coverage |
| Test files | 32 |
| Python source files | 20 |
| Open issues | 1 HIGH (verify_ssl) -- mypy resolved |
| ADR decisions | 9 |
| CI workflows | 2 (ci.yml + security job, release-please.yml) |
| Pre-commit hooks | detect-secrets, ruff, ruff-format |
| Dev container | .devcontainer/ |
| mypy | 0 errors |
