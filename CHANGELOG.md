# Changelog

## [0.7.2](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.1...v0.7.2) (2026-03-29)


### Bug Fixes

* complete credential redaction in test_live_nas.py; add .env.example for integration tests ([101baf7](https://github.com/by-openclaw/lib-synology-dsm/commit/101baf756449696d8f6005d0b2f683196a99076d))
* session complete — 100% coverage, integration report, ready for NAS testing ([2bcada9](https://github.com/by-openclaw/lib-synology-dsm/commit/2bcada935f315aa05fc0a30598e96a7e12e85979))

## [0.7.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.0...v0.7.1) (2026-03-29)


### Bug Fixes

* post-audit hardening complete — urllib migration, credential redaction, CI green ([c48f61b](https://github.com/by-openclaw/lib-synology-dsm/commit/c48f61b23d081f217cb0cdedcb9dcc62c8f24d93))

## [0.6.1] — 2026-03-29

### Added
- `FileStationManager.upload()`: now returns normalised dict with `skipped` flag (`overwrite=False` + file exists → `skipped: True`)
- `FileStationManager.list()`: supports `additional` parameter for per-file metadata (`size`, `time`, `owner`, `perm`, `real_path`, `type`)

## [0.6.0] — 2026-03-29

### Added
- `FileStationManager`: full File Station CRUD — `list_shares()`, `list()`, `mkdir()`, `upload()`, `download()`, `delete()`
- `docs/feature-coverage.md`: FileStation section updated — all operations ✅

### Fixed
- FileStation upload auth pattern corrected (discovered via browser DevTools):
  - `SynoToken` in URL query string, not request body
  - Session as cookie `id=`, not form field `_sid`
  - Upload field is `path`, not `dest_folder_path`
- `docs/feature-coverage.md`: FileStation was listed as 🚧 Planned — now reflects actual ✅ state

## [0.4.1] — 2026-03-28

### Fixed
- `client.py`: `X-SYNO-TOKEN` header now always sent when available — was missing on write ops, causing share create/delete to fail with 403 even with valid SID
- `groups.py`: Member management now uses `SYNO.Core.Group.set` with `members=` param instead of `member_set` (returns error 103 on DS1513+ DSM 7.x — invalid parameter)
- `tests/integration/test_live_nas.py`: `post()` helper now accepts `token=` param; `_api_raw()` and `api()` always send `X-SYNO-TOKEN`; login enables `synotoken` and stores it at module level; group member test updated to use correct `set` method

### Known remaining blocker
- `SYNO.Core.Share create` returns 403: `rune-api` user needs to be added to `administrators` group in DSM Control Panel → User & Group (one-time manual step)
- `rune-audit` account: error 402 (disabled) — re-enable in DSM UI



All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


### Added
- `DSMClient` — session lifecycle management via context manager
- `ShareManager` — shared folder CRUD and NFS permission management
- `NFSManager` — NFS export rule management
- `UserManager` — user/group CRUD with disable-not-delete pattern
- Unit tests for auth flow
- `pyproject.toml` with hatchling build system

## v0.7.0 (2026-03-29)

### Feat

- ensure() idempotency with diff detection and dry_run support
- typed exception hierarchy — DSMError, DSMAuthError, DSMPermissionError, DSMSessionError, DSMAPIError

## v0.6.1 (2026-03-29)

### Feat

- **filestation**: upload returns skipped flag, list supports additional properties

## v0.6.0 (2026-03-29)

### Feat

- **filestation**: add FileStationManager — upload, download, list, mkdir, delete
- **users**: add list_detailed() + get() — returns name, email, description, 2fa_enabled, expired, enabled; normalized for NetBox/Authentik
- **test**: add full CRUD bash test script; docs: update api-versions, api-reference, CLAUDE.md; bump to v0.5.0
- **idempotent**: add ensure(state=present/absent) to all managers — Ansible-style
- **crud**: add update() to UserManager, GroupManager, ShareManager
- **credentials**: add Vault + env credential providers; chore: ruff formatting; docs: api version reference
- **groups**: add GroupManager; fix(users): add group membership ops; fix(shares): correct API shape; test: live NAS integration test
- initial library structure — DSMClient, ShareManager, NFSManager, UserManager

### Fix

- **filestation**: correct upload auth — SynoToken in URL + cookie id + path field (DevTools verified)
- share create uses shareinfo JSON; NFS uses correct API; add bash CRUD test script
- X-SYNO-TOKEN required for all write ops; group member uses set not member_set
- **shares**: full CRUD + user/group permissions + NFS via compound requests; fix share_name param for NFS SharePrivilege
- **shares**: correct NFS API to SYNO.Core.FileServ.NFS.SharePrivilege (load/save); document name_org requirement for create
- **shares**: use shareinfo JSON object for create (DSM 7.x requirement); add set_permission(), create_with_permissions()
- **client**: add enable_syno_token=yes + X-SYNO-TOKEN header on all requests; docs(shares): document confirmed create/delete limitation
- **client**: use auth v7 + entry.cgi endpoint; fix(users): add delete() with JSON array format

[0.6.1]: https://github.com/by-openclaw/lib-synology-dsm/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/by-openclaw/lib-synology-dsm/compare/v0.4.1...v0.6.0
[0.4.1]: https://github.com/by-openclaw/lib-synology-dsm/releases/tag/v0.4.1
