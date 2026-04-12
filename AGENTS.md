# AGENTS.md — lib-synology-dsm

Python library for Synology DSM API — session auth, user/group/share/NFS CRUD, FileStation file ops, quota, bandwidth, traffic control, and storage management.

## Always Read First

Before touching anything in this repo:

1. [`README.md`](README.md) — library overview, usage, design decisions
2. [`CLAUDE.md`](CLAUDE.md) — agent-specific constraints, known blockers, API quirks
3. [`docs/feature-coverage.md`](docs/feature-coverage.md) — primary reference for implemented vs planned features
4. [`docs/api-versions.md`](docs/api-versions.md) — tested API version table (ground truth)
5. [`docs/api-reference.md`](docs/api-reference.md) — method reference with confirmed working signatures
6. [`src/synology_dsm/`](src/synology_dsm/) — library source
7. [`docs/refactor-clarification-2026-03-30.md`](docs/refactor-clarification-2026-03-30.md) — confirmed decisions and v1.0 priority matrix

## Mandatory reading before acting

Before writing, editing, or reviewing any file in this repo, read:

### doc-platform-core repo:
1. `/home/by-systems/repos/doc-platform-core/docs/standards/` — all standards files
2. `/home/by-systems/repos/doc-platform-core/docs/adr/` — all Accepted ADRs
3. The ADR template for your scope: `doc-platform-core/docs/templates/adr-template-infra.md`

### lib repos (lib-synology-dsm etc.):
1. `/home/by-systems/repos/lib-synology-dsm/docs/adr/` — lib-scoped ADRs only
2. The ADR template for your scope: `doc-platform-core/docs/templates/adr-template-lib.md`
3. Platform standards are NOT binding on lib repos — but lib CISO sections must reference them

### Rules:
- Do NOT infer. Do NOT invent policy. If a standard or ADR covers it — follow it.
- If you would override a standard — flag it with `[OVERRIDE REQUIRED]`, do NOT do it silently.
- Cross-ADR dependencies are FORBIDDEN. Each ADR is self-contained. Do not say "see ADR-XXXX".
- If content is relevant to two ADRs — each states it independently within its own scope.

## Current Milestone — v1.0

Target: stable public API, mypy clean, consistent return dicts across all managers.
v1.0 blockers: see CLAUDE.md v1.0 Blockers section and docs/refactor-clarification-2026-03-30.md section 5.

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
- **No httpx** — ADR-0001 decision: zero runtime deps — not a host availability constraint

## Project Health Rules (mandatory)

- **Test fails → open issue immediately.** Never fix silently. Issue first → fix → close with comment + commit ref.
- **Issue closed = CI green + specific test covers the fix.** No exceptions.
- **CI failure on main** that isn't already tracked → create a GitHub issue before anything else.
- **Every open issue** has a label, is on the Project board, has a linked commit or PR when closed.
- README reflects actual state — not aspirational. Update after every release.
- AGENTS.md + CLAUDE.md updated after every non-trivial change.

## What NOT To Do

> ⛔ **Also read `CLAUDE.md` §HARD RULES** — architectural decisions enforced there. AGENTS.md and CLAUDE.md are both authoritative. When in doubt, CLAUDE.md wins.

- ❌ Do NOT run live integration tests without first checking the DSM blocker below
- ❌ Do NOT publish to PyPI without explicit instruction from @yboujraf

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
| Open issues | 1 HIGH (verify_ssl) — mypy resolved |
| ADR decisions | 9 |
| CI workflows | 2 (ci.yml + security job, release-please.yml) |
| Pre-commit hooks | detect-secrets, ruff, ruff-format |
| Dev container | ✅ .devcontainer/ |
| mypy | ✅ 0 errors |

