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

## Current State (v0.8.0 — 2026-03-29)

| Component | Status |
|---|---|
| DSM auth (v7 + SynoToken) | ✅ working |
| User CRUD + ensure() | ✅ v0.7.0 |
| Group CRUD + membership + ensure() | ✅ v0.7.0 |
| Share CRUD + NFS permissions + ensure() | ✅ v0.7.0 |
| NFS ensure() per-client rule | ✅ v0.8.0 |
| FileStation: list/upload/download/mkdir/delete + ensure() | ✅ v0.8.0 |
| DSMConnectionError (network failures wrapped) | ✅ v0.7.3 |
| Exception hierarchy (DSMError → 6 typed exceptions) | ✅ v0.7.3 |
| dry_run support (all managers) | ✅ v0.7.0 |
| Unit tests (161 tests, 100% coverage) | ✅ v0.8.0 |
| CI: ruff + mypy + pytest on Python 3.10/3.11/3.12 | ✅ v0.7.1 |
| Coverage artifacts (htmlcov + coverage.xml, 30-day) | ✅ v0.7.2 |
| Pre-commit hooks (detect-secrets + ruff) | ✅ v0.7.3 |
| Dev container (.devcontainer/) | ✅ v0.7.3 |
| ADR: 3 decisions recorded | ✅ v0.7.3 |
| LICENSE (MIT) + disclaimer | ✅ v0.7.3 |
| Bash CRUD smoke test | ✅ tests/integration/dsm-crud-test.sh |
| Python integration test + --report flag | ✅ v0.7.2 |
| Ansible collection | ⏸ Phase 2 — see docs/ansible-roadmap.md |
| Vault AppRole auth | ⏸ Phase 2 — blocked until Vault deployed |
| Published to GitLab registry | ⏸ Phase 5 — blocked until GitLab CE deployed |

## Open issues

None. Zero open issues as of v0.8.0.

## Known DSM version bugs

### DSM 7.1.1-42962 Update 9 (DS1513+) — SYNO.Core.Group member_list broken
- `SYNO.Core.Group member_list` returns error 103 (invalid parameter) for ALL inputs
- This is a DSM 7.1.x regression — **fixed in DSM 7.2.x**
- Tracked in: GitHub issue #54 ("Upgrade DSM from 7.1.1 to 7.2.x")
- Impact: `add_member` / `remove_member` cannot verify idempotency — they apply unconditionally and return `warning` key
- Write operations (set with members=[]) work correctly — only read is broken
- Workaround: upgrade DSM to 7.2.x. Until then, operations are correct but not fully idempotent.

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
