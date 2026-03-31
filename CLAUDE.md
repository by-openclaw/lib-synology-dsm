> **Mandatory — read before any work:**
> 1. `workspace/OPERATING-STANDARD.md` — platform rules, quality gates, compliance
> 2. This file — repo-specific context

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

## ⛔ HARD RULES — Non-negotiable. Read before touching any file.

These are architectural decisions. They are NOT suggestions. Do not override them.

### HTTP client — urllib only (ADR-0001)
- **NEVER use `httpx`, `requests`, `aiohttp`, or any third-party HTTP library.**
- Use `urllib.request` exclusively. Zero runtime dependencies is a hard requirement.
- Rationale: ADR-0001 `docs/adr/0001-urllib-over-httpx.md`. Read it.
- If you think httpx is better — it doesn't matter. The decision is made.

### ensure() pattern on all managers (ADR-0002)
- Every manager MUST implement `ensure()` with fetch-diff-noop semantics.
- `ensure()` must return `{"changed": False}` when state already matches — never re-apply.
- `dry_run=True` must be supported on all destructive methods.
- Rationale: ADR-0002 `docs/adr/0002-ensure-pattern.md`.

### Credential providers — no hardcoded credentials (ADR-0003)
- Never hardcode credentials in source. Use `DSMCredentials`, `EnvCredentialProvider`, or `VaultCredentialProvider`.
- Rationale: ADR-0003 `docs/adr/0003-credential-provider-hierarchy.md`.

### TLS — verify_ssl default is PENDING DECISION
- `verify_ssl=False` is the current default but is under review.
- A platform-wide TLS/certificate strategy (naming convention, .arpa DNS, self-signed vs LE) must be decided first.
- Do NOT change the `verify_ssl` default without explicit confirmation from the owner.
- Track as open risk: `doc-platform-core/docs/raid.md`.

### Commit and version discipline
- All commits MUST follow Conventional Commits format.
- Release Please is the canonical release path. Do NOT run `scripts/release.sh` on this repo.
- Never manually edit version strings. Never run `cz bump` if Release Please is active.

### Definition of Done

Definition of Done: see SOUL.md (workspace) and CONTRIBUTING.md (checklist).

---

## v1.0 Blockers

| Priority | Blocker | Notes |
|---|---|---|
| ~~HIGH~~ | ~~FileStation.upload() returns {"skipped": bool} — violates ensure return dict standard~~ | ✅ Fixed — returns {"changed": bool, "action": str} |
| ~~HIGH~~ | ~~client.py timeout hardcoded at 30s — no per-operation timeout~~ | ✅ Fixed — configurable via DSMClient(timeout=N) |
| ~~HIGH~~ | ~~update()/disable() return None — violates ensure return dict standard~~ | ✅ Fixed — all return {"changed": bool, "action": str, "target": str} |
| ~~HIGH~~ | ~~mypy 27 errors — CI type check failing~~ | ✅ Fixed — 0 errors |
| ~~MEDIUM~~ | ~~verify_ssl=False default~~ | ✅ Decision: intentional platform default — no infra for self-signed/LE yet. Decided 2026-03-30. |

See: docs/refactor-clarification-2026-03-30.md section 5 Priority Matrix

---

## Current State (v0.10.1 — 2026-03-30)

| Component | Status |
|---|---|
| DSM auth (v7 + SynoToken) | ✅ working |
| User CRUD + ensure() | ✅ v0.7.0 |
| Group CRUD + membership + ensure() | ✅ v0.7.0 |
| Share CRUD + NFS permissions + ensure() | ✅ v0.7.0 |
| NFS ensure() per-client rule | ✅ v0.8.0 |
| FileStation: list/upload/download/mkdir/delete + ensure() | ✅ v0.8.0 — download() returns {changed, action} (v0.10.1) |
| Quota manager | ✅ v0.9.0 |
| Bandwidth manager (read + write + ensure_user/ensure_group) | ✅ v0.9.0 |
| TrafficControlManager (CRUD + ensure_rule) | ✅ v0.9.0 |
| Storage manager | ✅ v0.9.0 |
| DSMConnectionError (network failures wrapped) | ✅ v0.7.3 |
| Exception hierarchy (DSMError → 6 typed exceptions) | ✅ v0.7.3 |
| dry_run support (all managers) | ✅ v0.7.0 |
| Unit tests (345 passing, 100% coverage) | ✅ v0.10.3 |
| CI: ruff + mypy + pytest on Python 3.10/3.11/3.12/3.13 | ✅ CI active |
| CI scope: `src/synology_dsm/` + `tests/unit/` + `tests/integration/` only (v2 WIP excluded) | ✅ 2026-03-31 |
| CI: Bandit SAST + pip-audit CVE gate | ✅ 2026-03-29 |
| Coverage artifacts (htmlcov + coverage.xml, 30-day) | ✅ v0.7.2 |
| Pre-commit hooks (detect-secrets + ruff) | ✅ v0.7.3 |
| Dev container (.devcontainer/) | ✅ v0.7.3 |
| ADR: 9 decisions recorded | ✅ v0.10.3 |
| LICENSE (MIT) + disclaimer | ✅ v0.7.3 |
| mypy — 0 errors | ✅ v0.10.x |
| Ansible collection | ⏸ Phase 2 — see docs/ansible-roadmap.md |
| Vault AppRole auth | ⏸ Phase 2 — blocked until Vault deployed |
| Published to GitLab registry | ⏸ Phase 5 — blocked until GitLab CE deployed |

## Open issues (as of 2026-03-30 audit)

| Priority | Issue | Tracking |
|---|---|---|
| ~~HIGH~~ | ~~mypy 27 errors — CI red on type check~~ | ✅ Fixed — 0 errors |
| HIGH | verify_ssl=False default — pending TLS strategy decision | Blocked on platform cert/DNS decision |
| ~~HIGH~~ | ~~FileStation.upload() returns {"skipped": bool} — violates ensure return dict~~ | ✅ Fixed |
| ~~HIGH~~ | ~~client.py timeout hardcoded at 30s — no per-operation timeout~~ | ✅ Fixed |
| MEDIUM | API reference lags code — missing list_detailed, add/remove_member | Backlog |
| MEDIUM | README stale — test count + Python 3.13 badge missing | Backlog |
| MEDIUM | build not in dev deps — wheel/sdist not CI-validated | Backlog |
| ~~MEDIUM~~ | ~~Two release paths (commitizen + release-please)~~ | ✅ Resolved — Release Please is canonical |

---

## Key Files

| File | Why |
|---|---|
| `README.md` | Install, quickstart, API reference |
| `src/synology_dsm/` | v1 library source (stable) |
| `src/synology_dsm_v2/` | v2 WIP — OOB design patterns (in progress, CI-excluded until ready) |
| `tests/unit/` + `tests/integration/` | v1 tests |
| `tests/unit_v2/` + `tests/integration_v2/` | v2 tests (CI-excluded until ready) |
| `CHANGELOG.md` | Semantic versioning history |

---

## API gotchas (read before touching any FileStation or Core code)

- ALL write ops require `X-SYNO-TOKEN` header — missing it returns 403
- Share create: must use `shareinfo` JSON object, not flat params
- Group members: use `SYNO.Core.Group.set` with `members=[]`, NOT `member_set` (error 103)
- NFS rules: use `SYNO.Core.FileServ.NFS.SharePrivilege.save`, NOT `SYNO.Core.Share.NFS` (error 102)
- **FileStation upload**: `SynoToken` in URL query string only; session as cookie `id=`; field `path` not `dest_folder_path` — do NOT bypass `FileStationManager`
- User/Group delete: name must be a JSON array string: `'["name"]'`

---

## Known DSM version bugs

### DSM 7.1.1-42962 Update 9 (DS1513+) — SYNO.Core.Group member_list broken
- `SYNO.Core.Group member_list` returns error 103 (invalid parameter) for ALL inputs
- This is a DSM 7.1.x regression — **fixed in DSM 7.2.x**
- Tracked in: GitHub issue #54 ("Upgrade DSM from 7.1.1 to 7.2.x")
- Impact: `add_member` / `remove_member` cannot verify idempotency — they apply unconditionally and return `warning` key
- Write operations (set with members=[]) work correctly — only read is broken
- Workaround: upgrade DSM to 7.2.x. Until then, operations are correct but not fully idempotent.

---

## Constraints

- Never commit DSM credentials or API tokens
- `tests/` must pass before any merge to `main`
- Breaking changes = MAJOR version bump + migration note in CHANGELOG
- `ruff` linting must be clean before commit (v1 scope only; v2 WIP is CI-excluded)
- Do NOT add `src/synology_dsm_v2/` or `tests/unit_v2/` to CI scope until v2 sprint is complete
- `mypy` must be clean before commit (0 errors as of 2026-03-30)

---

## Cross-repo References

- Naming convention: see `doc-platform-core/docs/adr/0010-naming-and-identity-convention.md`
- Environment tiers: poc/dev/test/staging/acc/prod — always explicit. See `doc-platform-core/docs/adr/0012-environment-tier-standard.md`

---

## Related

- Platform charter: `doc-platform-core/docs/adr/0006-platform-charter.md`
- RAID: `doc-platform-core/docs/raid.md`
- GitHub Issues: <https://github.com/by-openclaw/lib-synology-dsm/issues>
- Refactor decisions: docs/refactor-clarification-2026-03-30.md section 6 Decisions Log
