# AGENTS.md — lib-synology-dsm

Python library for Synology DSM API automation — session management, user/group/share CRUD, NFS export rules, and FileStation file operations (upload/download/list/mkdir/delete).

## Always Read First

Before touching anything in this repo:

1. [`README.md`](README.md) — library overview, usage, design decisions
2. [`CLAUDE.md`](CLAUDE.md) — agent-specific constraints, known blockers, API quirks
3. [`docs/feature-coverage.md`](docs/feature-coverage.md) — primary reference for implemented vs planned features
4. [`docs/api-versions.md`](docs/api-versions.md) — tested API version table (ground truth)
5. [`docs/api-reference.md`](docs/api-reference.md) — method reference with confirmed working signatures
6. [`src/synology_dsm/`](src/synology_dsm/) — library source

## Coding & Commit Standards

- **Conventional Commits** — `type(scope): description`
  - `feat(shares): add NFS rule deletion`
  - `fix(client): handle synotoken expiry on long sessions`
  - `test(integration): add live share CRUD test`
  - `docs(api-reference): document group membership API`
- **Python style:** PEP 8, type hints on all public methods
- **Version:** `pyproject.toml` — bump with `feat` or `fix` commits per semver
- **Branch naming:** `feat/{issue-id}-{description}` or `fix/{issue-id}-{description}`
- **All new managers** must implement `ensure(state=present|absent)` idempotent pattern
- **No httpx** — integration tests use `urllib` only (httpx not available on Rune's host)

## Project Health Rules (mandatory)

- **Test fails → open issue immediately.** Never fix silently. Issue first → fix → close with comment + commit ref.
- **Issue closed = CI green + specific test covers the fix.** No exceptions.
- **CI failure on main** that isn't already tracked → create a GitHub issue before anything else.
- **Every open issue** has a label, is on the Project board, has a linked commit or PR when closed.
- README reflects actual state — not aspirational. Update after every release.
- AGENTS.md + CLAUDE.md updated after every non-trivial change.

## What NOT To Do

- ❌ Do NOT use `httpx` — use `urllib` for all HTTP calls
- ❌ Do NOT use `auth.cgi` — always use `entry.cgi` for SYNO.API.Auth v6
- ❌ Do NOT skip `X-SYNO-TOKEN` header on write requests
- ❌ Do NOT check top-level `success` for compound requests — check `data.has_fail`
- ❌ Do NOT use `sharename` param for NFS API — use `share_name` (causes error 2301)
- ❌ Do NOT omit `name_org` in `shareinfo` JSON — causes HTTP 403 on DSM 7.x
- ❌ Do NOT run live integration tests without first checking the DSM blocker below
- ❌ Do NOT publish to PyPI without explicit instruction from My Lord

## Known Blocker

**DSM account requirements for integration tests:**

Admin account (`API_USER` / e.g. `rune-api`):
- Group: `administrators`
- Applications: DSM = **Allow**, File Station = **Allow**

Audit account (`AUDIT_USER` / e.g. `rune-audit`):
- Group: `users` (no admin rights)
- Applications: DSM = **Allow**, File Station = **Allow** (needed for section 7 FileStation list tests)
- Note: error 402 on login = account disabled in DSM Control Panel → User & Group → Edit → Enable

## GitHub Repo

<https://github.com/by-openclaw/lib-synology-dsm>

## Agent: Rune

Maintained by Rune (DevOps familiar) for the BY-SYSTEMS PoC platform.
Owner: @yboujraf

## Doc Maintenance — After Every Successful Build

After each successful CI build (all jobs green), update these files to reflect current state:
- **AGENTS.md** — Update "Project Stats", version, checklist, roadmap progress
- **CLAUDE.md** — Update build commands, file table, current state if anything changed
- **README.md** — Update badges, feature lists, version numbers

Commit separately: `docs: update project docs to v{version}`

This ensures any AI agent (or human) picking up the project always has accurate, current documentation.

---

## Project Stats

> Auto-updated on every release. Last updated: 2026-03-29

| Metric | Value |
|---|---|
| Version | v0.8.0 |
| Tagged releases | 6 |
| Unit tests | 170 passing, 100% coverage |
| Open issues | 0 |
| ADR decisions | 3 |
| CI workflows | 2 (ci.yml, release-please.yml) |
| Pre-commit hooks | detect-secrets, ruff, ruff-format |
| Dev container | ✅ .devcontainer/ |

