# OPERATING-STANDARD.md

Operating rules for lib-synology-dsm. Authoritative alongside `CLAUDE.md` and `AGENTS.md`.
When rules conflict, precedence: `CLAUDE.md` > `OPERATING-STANDARD.md` > `AGENTS.md`.

---

## Branch Naming

Every change must be on a branch — **never commit directly to `main`**.

| Type | Pattern | Example |
|---|---|---|
| Feature | `feat/{issue-id}-{short-description}` | `feat/33-system-manager` |
| Bug fix | `fix/{issue-id}-{short-description}` | `fix/30-auth-cgi-v7` |
| Docs only | `docs/{issue-id}-{short-description}` | `docs/27-feature-coverage-update` |
| Chore/refactor | `chore/{issue-id}-{short-description}` | `chore/15-drop-deprecated-list-groups` |

Rules:
- `{issue-id}` is the GitHub issue number — always link branch to an issue
- `{short-description}` is kebab-case, max 5 words
- No branch = no PR = no merge. No exceptions.

---

## Pull Request Workflow

1. Create issue (if not already exists) → get issue number
2. Create branch from `main`: `git checkout -b fix/30-auth-cgi-v7`
3. Implement + tests + CHANGELOG entry + version bump
4. Push branch + open PR targeting `main`
5. PR description must include: what changed, why, issue ref (`Closes #N`), test evidence
6. CI must be green before merge
7. Merge via squash or merge commit — no force-push to `main`
8. Tag version after merge: `git tag vX.Y.Z && git push origin vX.Y.Z`

---

## Commit Convention

Follows Conventional Commits. Format: `type(scope): description`

| Type | Bump | When |
|---|---|---|
| `fix` | patch | Bug fix |
| `feat` | minor | New feature |
| `fix!` / `feat!` / `BREAKING CHANGE` | major | Breaking change |
| `docs` | none | Documentation only |
| `chore` | none | Tooling, CI, housekeeping |
| `test` | none | Test-only changes |
| `refactor` | none | Code restructure, no behavior change |

Scope = module name: `client`, `exceptions`, `users`, `shares`, `filestation`, `quota`, `bandwidth`, `nfs`, `storage`, `trafficcontrol`.

---

## Definition of Done

A fix or feature is **done** when:

- [ ] Code implemented and linted (`ruff check`, `ruff format --check`)
- [ ] Type-annotated — mypy clean (`mypy src/`)
- [ ] Unit tests added/updated — `pytest tests/unit/` passes
- [ ] Smoke tests pass — `pytest tests/smoke/`
- [ ] Integration tests run on live NAS and pass (where applicable)
- [ ] `CHANGELOG.md` has entry under correct version section
- [ ] `pyproject.toml` version bumped
- [ ] `src/synology_dsm/__init__.py` `__version__` bumped
- [ ] `docs/feature-coverage.md` updated (if feature surface changed)
- [ ] PR opened, CI green, merged
- [ ] GitHub issue closed with comment: what was done, which commit, which tests cover it
- [ ] Version tag pushed

Nothing ships at 60%.

---

## API References (precedence order)

When implementing a new manager, consult these in order:

1. **Official Synology KB** — <https://kb.synology.com/en-us/DG/DSM_Login_Web_API_Guide/2>
2. **pmilano1/synology-dsm-api** — <https://github.com/pmilano1/synology-dsm-api/tree/master/docs/api-reference> (community spec mirror)
3. **n4s4/synology-api** — <https://n4s4.github.io/synology-api/docs/apis> (working Python implementation — reference for request/response shape)

Use n4s4 for implementation patterns only. Do NOT copy their code or adopt their dependencies (ADR-0001: zero runtime deps).

---

## Architecture Constraints (non-negotiable)

- **Zero runtime dependencies** — stdlib only (ADR-0001). `httpx`, `requests`, `aiohttp` are banned.
- **All managers return `{changed: bool, action: str}`** — consistent return pattern, no exceptions.
- **`ensure()` is mandatory** on every manager — idempotent, `state=present|absent`, `dry_run` support.
- **No direct `main` commits** — see Branch Naming above.
- **No PyPI publish** without explicit instruction from @yboujraf.
- **No live integration tests** without verifying DSM account permissions (see `docs/feature-coverage.md` → Account Permission Requirements).

---

## Error Handling

All API errors map to typed exceptions. See `src/synology_dsm/exceptions.py` and the error map in `client.py`.

| Code range | Exception | Notes |
|---|---|---|
| 400, 401, 402 | `DSMAuthError` | Auth failures |
| 103, 403 | `DSMPermissionError` | Permission denied |
| 105, 106, 119 | `DSMSessionError` | Session expired/invalid |
| 404 | `DSMNotFoundError` | Resource not found |
| 117 | `DSMInvalidOperationError` | Invalid state for operation |
| 100–102, 120, 1001, 1009, 1010 | `DSMInvalidParameterError` | Bad params |
| network | `DSMConnectionError` | Cannot reach NAS |
| other | `DSMAPIError` | Generic fallback |

Reference: <https://github.com/pmilano1/synology-dsm-api/blob/master/docs/guides/error-handling.md>

---

## Version Tracking

`pyproject.toml`, `src/synology_dsm/__init__.py.__version__`, and `CHANGELOG.md` must always be in sync.
Tags: `vX.Y.Z` — pushed after every release.

---

_Last updated: 2026-03-31 — created from scattered rules in AGENTS.md, CLAUDE.md, CONTRIBUTING.md_
