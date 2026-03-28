# CLAUDE.md — lib-synology-dsm

> **Scope:** `lib` | **Component:** `synology-dsm`
> **GitHub:** `by-openclaw/lib-synology-dsm`
> **Layer:** Layer 4 — Storage (ADR-0006)

AI agent context. Read before touching any file.

---

## What This Repo Does

Python library for Synology DSM API — CRUD for users, groups, permissions, and shared folders.
Published as a versioned package; consumed as a dependency by platform-setup and other tools.

**NOT for:** direct deployment, VM provisioning, or any infra changes.

---

## Key Files

| File | Why |
|---|---|
| `README.md` | Install, quickstart, API reference |
| `synology_dsm/` | Library source |
| `tests/` | Unit + integration tests |
| `CHANGELOG.md` | Semantic versioning history |

---

## Current State

| Component | Status |
|---|---|
| DSM user CRUD | ✅ implemented |
| Shared folder management | ✅ implemented |
| CI tests | ⏸ blocked |
| Published to registry | ⏸ blocked pending GitLab CE |

## Blocker

`rune-api` DSM user needs **Application → DSM = Allow** set in Synology UI before integration tests can run.
See RAID D-002.

---

## Constraints

- Never commit DSM credentials or API tokens
- `tests/` must pass before any merge to `main`
- Breaking changes = MAJOR version bump + migration note in CHANGELOG
- `ruff` linting must be clean before commit

---

## Diagram Standard

See ADR-0006 §9. Source → `assets/diagrams/`, render → `assets/exports/`, commit + post to Discord.

---

## Related

- Platform charter: `doc-platform-core/docs/adr/0006-platform-charter.md`
- RAID: `doc-platform-core/docs/raid.md`
- GitHub Issues: <https://github.com/by-openclaw/platform-setup/issues>
