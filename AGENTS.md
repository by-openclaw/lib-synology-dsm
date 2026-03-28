# AGENTS.md — lib-synology-dsm

Python library for Synology DSM API automation — session management, user/group/share CRUD, and NFS export rules.

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

**rune-api DSM user:** Needs `Application → DSM = Allow` set in Synology Control Panel → User before live integration tests will pass.

## GitHub Repo

<https://github.com/by-openclaw/lib-synology-dsm>

## Agent: Rune

Maintained by Rune (DevOps familiar) for the BY-SYSTEMS PoC platform.
Owner: @yboujraf
