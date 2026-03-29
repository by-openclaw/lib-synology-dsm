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

## Current State (v0.7.0 — 2026-03-29)

| Component | Status |
|---|---|
| DSM auth (v7 + SynoToken) | ✅ working |
| User CRUD | ✅ working |
| Group CRUD + membership | ✅ working |
| Share CRUD | ✅ working |
| NFS permissions | ✅ working (DSM 7.x API fixed) |
| FileStation: list/upload/download/mkdir/delete | ✅ working |
| Exception hierarchy (DSMError → typed) | ✅ v0.7.0 |
| ensure() idempotency + noop detection | ✅ v0.7.0 |
| dry_run support (all managers + FileStation) | ✅ v0.7.0 |
| Unit tests (45 tests, 100%) | ✅ v0.7.0 |
| Commitizen + Conventional Commits | ✅ v0.7.0 |
| Bash CRUD smoke test | ✅ `tests/integration/dsm-crud-test.sh` |
| Python integration test | ✅ 17/19 (2 non-blocking warnings) |
| CI tests | ⏸ blocked pending GitLab CE |
| Published to registry | ⏸ blocked pending GitLab CE |

## Remaining warnings (non-blocking)

- `rune-audit` account: error 402 (disabled in DSM) — re-enable in Control Panel → User & Group

## API gotchas (read before touching any FileStation or Core code)

- ALL write ops require `X-SYNO-TOKEN` header — missing it returns 403
- Share create: must use `shareinfo` JSON object, not flat params
- Group members: use `SYNO.Core.Group.set` with `members=[]`, NOT `member_set` (error 103)
- NFS rules: use `SYNO.Core.FileServ.NFS.SharePrivilege.save`, NOT `SYNO.Core.Share.NFS` (error 102)
- **FileStation upload**: `SynoToken` in URL query string only; session as cookie `id=`; field `path` not `dest_folder_path` — do NOT bypass `FileStationManager`
- User/Group delete: name must be a JSON array string: `'["name"]'`

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
