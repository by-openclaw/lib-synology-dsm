# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-03-28

### Fixed
- `shares.py`: Share create now uses `shareinfo` JSON object with `name_org` field (DSM 7.x requirement)
- `shares.py`: NFS API corrected to `SYNO.Core.FileServ.NFS.SharePrivilege` with `share_name` param
- `client.py`: Auth now uses `enable_syno_token=yes` and sends `X-SYNO-TOKEN` header on all write requests

### Added
- `shares.py`: `create_with_permissions()` — full share lifecycle in one call (create + user perms + group perms + NFS)
- `shares.py`: `set_permission()` — user/group ACL on shares
- `tests/integration/test_full_crud.sh` — comprehensive bash test script for all CRUD operations

## [0.4.0] - 2026-03-27

### Added
- `update()` method on UserManager, GroupManager, ShareManager — wraps DSM `set` API
- `ensure(state="present"/"absent")` on all three managers — idempotent, Ansible-style
- `docs/feature-coverage.md` — full API coverage table (implemented vs planned)
- `docs/references.md` — official + community API documentation links
- `CLAUDE.md` — agent/developer notes for this repo
- API references added to README.md

## [0.3.0] - 2026-03-27

### Added
- `credentials.py` — `EnvCredentialProvider`, `VaultCredentialProvider`, `get_credentials()`
- `.env.example` — template for local development
- `docs/credentials.md` — credential provider documentation
- `docs/api-versions.md` — API version reference table

### Changed
- PEP8 / ruff formatting applied across all source files
- `pyproject.toml` — added `[vault]` optional dependency group with `hvac`
- `.gitignore` — added `.env`, `.venv/`, cache dirs

### Security
- `.env` excluded from git via `.gitignore`
- Vault provider as first-class credential source for production use

## [0.2.0] - 2026-03-27

### Added
- `GroupManager` (`src/synology_dsm/groups.py`) — full group CRUD and membership ops
  - `list()`, `create()`, `delete()`, `get()`, `add_member()`, `remove_member()`, `list_members()`
  - `delete()` uses JSON array format matching DSM API requirement (same as `UserManager.delete`)
  - `add_member()` / `remove_member()` fetch current members first to avoid overwriting
  - `list_members()` falls back to `get` if `member_list` unavailable (DSM version dependent)
- `UserManager.add_to_group()` — delegates to `GroupManager.add_member()`
- `UserManager.remove_from_group()` — delegates to `GroupManager.remove_member()`
- `ShareManager.get_nfs_rules()` — retrieve existing NFS rules before overwriting
- Integration test: `tests/integration/test_live_nas.py` — urllib-only, validates full API contract
  against live NAS (no httpx dependency)
- `__init__.py` now exports `GroupManager`, `ShareManager`, `UserManager`

### Fixed
- `ShareManager.list()` now passes `additional` as JSON array string (was missing in some code paths)
- `ShareManager.set_nfs_permission()` now accepts `squash` and `async_io` parameters with correct
  JSON shape — verified against DSM 7.1.1 live NAS
- `ShareManager.create()` / `delete()` docstrings now clearly document admin privilege requirement
  (returns HTTP 403 if user is not in `administrators` group)
- All managers now include docstrings explaining DSM API quirks found during live testing

### Known Issues / Live Test Findings
- `SYNO.Core.Group.member_set` returns code 103 (method not implemented) on DSM 7.1.1 for
  non-administrator sessions. Use admin session (`session=DSM`, user in `administrators` group).
- `SYNO.FileStation.List.list /` returns 401 — must specify a valid share path, not bare `/`.
- `rune-audit` account was disabled on NAS (error 402 on login) — must be re-enabled in
  DSM Control Panel → User & Group before audit/read-only tests pass.
- `SYNO.Core.Share.create` returns HTTP 403 unless API user is in `administrators` group.
  To fix: add `rune-api` to `administrators` group in DSM Control Panel.

## [0.1.0] - 2026-03-27

### Added
- `DSMClient` — session lifecycle management via context manager
- `ShareManager` — shared folder CRUD and NFS permission management
- `NFSManager` — NFS export rule management
- `UserManager` — user/group CRUD with disable-not-delete pattern
- Unit tests for auth flow
- `pyproject.toml` with hatchling build system
