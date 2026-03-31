# Sprint: v2 Library Development — 4 Ansible-critical Managers

> **Repo:** lib-synology-dsm
> **Scope:** `src/synology_dsm_v2/` + `tests/unit_v2/` + `tests/integration_v2/`
> **Proven pattern:** CoreUserManager (127 unit + 14 integration tests, all green)
> **Executor:** Team agent
> **Auditor:** Claude Opus
> **Rule:** Do NOT touch `src/synology_dsm/` or `tests/unit/` — v1 stays untouched

---

## What's done (v2 PoC — proven)

```
src/synology_dsm_v2/
  base.py          ← BaseManager ABC, ClientProtocol, State, Action, EnsureResult
  client.py        ← DSMClient with properties, __repr__, error code map + descriptions
  exceptions.py    ← 9-class hierarchy, ERROR_MAP, ERROR_DESCRIPTIONS
  core_user.py     ← CoreUserManager — reference implementation (127 unit + 14 integration tests)
```

**Pattern per manager: 3 public methods only**
- `list()` — read all resources
- `get(name)` — read one resource
- `ensure(name, state, dry_run, **kwargs)` — create/update/delete (the ONLY write method)

**Internal CRUD is private:** `_create()`, `_update()`, `_delete()` — called by ensure() only.

**DI via constructor:** `super().__init__(client, api="SYNO.Core.User", version=1)`

---

## What to build (4 managers)

### Manager 1: CoreGroupManager

| Field | Value |
|---|---|
| File | `src/synology_dsm_v2/core_group.py` |
| API | `SYNO.Core.Group` v1 |
| Diff fields | `description` |
| Extra private methods | `_add_member(group, username)`, `_remove_member(group, username)`, `_list_members(group)` |
| ensure() handles | Create group, update description, delete group, add/remove members via kwargs `members=["alice","bob"]` |
| Test file | `tests/unit_v2/test_core_group.py` |
| Integration | `tests/integration_v2/test_live_groups.py` |
| Copy from | `core_user.py` — change API, diff fields, add membership logic |

**Known DSM quirk:** `SYNO.Core.Group.Member list` returns error 103 on DSM 7.1.x. Use fallback chain: `Member.list(ingroup=true)` → `Group.member_list` → `Group.get` + parse members field. See v1 `groups.py` lines 174-213.

### Manager 2: CoreShareManager

| Field | Value |
|---|---|
| File | `src/synology_dsm_v2/core_share.py` |
| API | `SYNO.Core.Share` v1 |
| Diff fields | `description`, `vol_path` |
| Extra private methods | None for base share CRUD. Permission + NFS are separate managers. |
| ensure() handles | Create share (with `vol_path`), update description, delete share |
| Test file | `tests/unit_v2/test_core_share.py` |
| Integration | `tests/integration_v2/test_live_shares.py` |
| Copy from | `core_user.py` |

**Known DSM quirk:** Share create uses `shareinfo` JSON object, not flat params. Share delete requires JSON array `'["name"]'`. See v1 `shares.py`.

### Manager 3: CoreFileServNFSManager

| Field | Value |
|---|---|
| File | `src/synology_dsm_v2/core_fileserv_nfs.py` |
| API | `SYNO.Core.FileServ.NFS.SharePrivilege` v1 |
| Diff fields | `hostname`, `rw`, `root_squash`, `async_io` |
| ensure() handles | ensure per hostname per share — add/update/remove NFS rule |
| Test file | `tests/unit_v2/test_core_fileserv_nfs.py` |
| Integration | `tests/integration_v2/test_live_nfs.py` |
| Copy from | `core_user.py` — ensure logic is per-hostname, not per-name |

**ensure() signature is different:**
```python
def ensure(self, share_name: str, hostname: str, state: State, dry_run: bool = False, **kwargs) -> EnsureResult:
```

### Manager 4: FileStationManager

| Field | Value |
|---|---|
| File | `src/synology_dsm_v2/filestation.py` |
| API | `SYNO.FileStation.List` v2 (list), `SYNO.FileStation.CreateFolder` v2, `SYNO.FileStation.Delete` v2, `SYNO.FileStation.Upload` v3, `SYNO.FileStation.Download` v2 |
| Diff fields | N/A — file operations don't diff, they check existence |
| Extra private methods | `_upload(local_path, dest)`, `_download(remote, local)`, `_mkdir(parent, name)`, `_delete(path)`, `_build_multipart()` |
| ensure() handles | Ensure folder exists (create if missing, noop if present, delete if absent) |
| Test file | `tests/unit_v2/test_filestation.py` |
| Integration | `tests/integration_v2/test_live_filestation.py` |
| Copy from | v1 `filestation.py` for multipart upload logic |

**This is the only HIGH complexity manager** — multipart upload with custom boundary encoding, SynoToken in URL query, session as cookie. The ensure() pattern is the same, but `_upload()` has special HTTP handling.

**Note:** FileStation uses MULTIPLE APIs (List, CreateFolder, Delete, Upload, Download). The BaseManager `_request()` helper uses `self._api` — but FileStation needs to call different APIs per method.

**DECISION (2026-03-31, @yboujraf):** Use `self._client.request(api="SYNO.FileStation.Xxx", ...)` directly for non-primary APIs. Do NOT override `_request()` — the BaseManager ABC contract stays clean. This is the only acceptable exception to the DI pattern and must be documented with a comment in the code.

---

## Execution order

```
Step 1: CoreGroupManager
  - Copy core_user.py → core_group.py
  - Change API, diff fields, add membership private methods
  - Write tests (unit + integration)
  - Commit: feat(v2): CoreGroupManager — SYNO.Core.Group

Step 2: CoreShareManager
  - Copy core_user.py → core_share.py
  - Change API, diff fields, handle shareinfo JSON
  - Write tests
  - Commit: feat(v2): CoreShareManager — SYNO.Core.Share

Step 3: CoreFileServNFSManager
  - Copy core_user.py → core_fileserv_nfs.py
  - Change API, ensure per hostname
  - Write tests
  - Commit: feat(v2): CoreFileServNFSManager — SYNO.Core.FileServ.NFS

Step 4: FileStationManager
  - Copy v1 multipart logic
  - Adapt to v2 pattern (BaseManager, EnsureResult, private CRUD)
  - Write tests
  - Commit: feat(v2): FileStationManager — SYNO.FileStation

Step 5: Update __init__.py + run all tests
  - Add all 4 new managers to exports
  - Run: .venv/bin/python3 -m pytest tests/unit_v2/ tests/integration_v2/ -v
  - All must pass
  - Commit: feat(v2): export all 5 managers

Step 6: Update docs
  - Update api-namespace-coverage.md
  - Update design-v2-poc.md success criteria
  - Commit: docs(v2): update coverage and design doc
```

---

## Credentials for integration tests

Read from: `~/.openclaw/workspace/infra/secrets/infra-synology-nas.json`

The integration test runner (`tests/integration_v2/test_live_users.py`) already loads from this path. New integration tests follow the same pattern.

---

## Rules

- Follow `OPERATING-STANDARD.md`
- 3 public methods per manager: `list()`, `get()`, `ensure()`
- CRUD is private: `_create()`, `_update()`, `_delete()`
- DI via constructor: `super().__init__(client, api="SYNO.Core.Xxx", version=N)`
- All API calls via `self._request(method, **params)` — inherited from BaseManager
- Class naming: API namespace in PascalCase + Manager (e.g., `SYNO.Core.Group` → `CoreGroupManager`)
- Module naming: lowercase with underscores (e.g., `core_group.py`)
- Error handling: typed exceptions from ERROR_MAP, never raw urllib errors
- ensure() returns `EnsureResult`, never `dict`
- Tests: unit (mocked) + integration (live NAS)
- No `# pragma: no cover` without explicit reason

---

## Success criteria

- [ ] 5 managers in `src/synology_dsm_v2/` (User + Group + Share + NFS + FileStation)
- [ ] All managers follow BaseManager ABC (list, get, ensure only)
- [ ] All CRUD is private (_create, _update, _delete)
- [ ] All ensure() returns EnsureResult with correct Action enum
- [ ] All dry_run tested (unit + integration)
- [ ] All error codes produce typed exceptions
- [ ] Unit tests: 100% coverage on v2 modules
- [ ] Integration tests: full lifecycle (create → noop → update → dry_run → delete → absent noop)
- [ ] `__init__.py` exports all 5 managers
- [ ] api-namespace-coverage.md updated

---

*Read this sprint plan + design-v2-poc.md + core_user.py (the reference). Copy the pattern. Don't reinvent.*
