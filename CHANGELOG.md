# Changelog

## 0.1.0 (2026-03-29)


### Features

* **credentials:** add Vault + env credential providers; chore: ruff formatting; docs: api version reference ([124b7e5](https://github.com/by-openclaw/lib-synology-dsm/commit/124b7e589125f7ecd7dad574cc3f3230e2c4860d))
* **crud:** add update() to UserManager, GroupManager, ShareManager ([a6f1e82](https://github.com/by-openclaw/lib-synology-dsm/commit/a6f1e8247c9e39657d0845307a1ae6e52e6628cc))
* ensure() idempotency with diff detection and dry_run support ([f99b08d](https://github.com/by-openclaw/lib-synology-dsm/commit/f99b08d821121c9e263204c7360c991309e4b0c2))
* **filestation:** add FileStationManager — upload, download, list, mkdir, delete ([cb6b72b](https://github.com/by-openclaw/lib-synology-dsm/commit/cb6b72bb14611b90ff2a13d3b4cbf4cd93de5ddc))
* **filestation:** upload returns skipped flag, list supports additional properties ([cc7fd09](https://github.com/by-openclaw/lib-synology-dsm/commit/cc7fd09076c6a2db1466e27c28b75487ac870be9))
* **groups:** add GroupManager; fix(users): add group membership ops; fix(shares): correct API shape; test: live NAS integration test ([687425a](https://github.com/by-openclaw/lib-synology-dsm/commit/687425a5faee0a5d3335d6a923c720c6a3328ed5))
* **idempotent:** add ensure(state=present/absent) to all managers — Ansible-style ([966a7db](https://github.com/by-openclaw/lib-synology-dsm/commit/966a7dbccda29ff2eea81cfbc5c9b64f9a851eb4))
* initial library structure — DSMClient, ShareManager, NFSManager, UserManager ([13a258a](https://github.com/by-openclaw/lib-synology-dsm/commit/13a258a43fc03dc0fc04d6b97fca683ec83881d6))
* **test:** add full CRUD bash test script; docs: update api-versions, api-reference, CLAUDE.md; bump to v0.5.0 ([1a8208a](https://github.com/by-openclaw/lib-synology-dsm/commit/1a8208a64a88f5da93db5b9e6142b913d1eca329))
* typed exception hierarchy — DSMError, DSMAuthError, DSMPermissionError, DSMSessionError, DSMAPIError ([eb47e0e](https://github.com/by-openclaw/lib-synology-dsm/commit/eb47e0e1dd62ce93bb67ca7756ac0f6c8e0afb40))
* **users:** add list_detailed() + get() — returns name, email, description, 2fa_enabled, expired, enabled; normalized for NetBox/Authentik ([98c3c7d](https://github.com/by-openclaw/lib-synology-dsm/commit/98c3c7d426d2b07e7272c31f03b91268ad705352))


### Bug Fixes

* CI — run tests/unit/ only; remove stale tests/test_client.py; integration tests require live NAS ([d136399](https://github.com/by-openclaw/lib-synology-dsm/commit/d136399254ec5247fd191c96bc909de1e3568505))
* **client:** add enable_syno_token=yes + X-SYNO-TOKEN header on all requests; docs(shares): document confirmed create/delete limitation ([e0e6cd8](https://github.com/by-openclaw/lib-synology-dsm/commit/e0e6cd8d6113786f1c62f50d4341f1ec48fe74a4))
* **client:** use auth v7 + entry.cgi endpoint; fix(users): add delete() with JSON array format ([197cd74](https://github.com/by-openclaw/lib-synology-dsm/commit/197cd745b8257dcd8e2e6989fdaf22ddf8a8809a))
* **filestation:** correct upload auth — SynoToken in URL + cookie id + path field (DevTools verified) ([07c487f](https://github.com/by-openclaw/lib-synology-dsm/commit/07c487f3bb0b4b01dda2dea9155ed2e52e9e7cb5))
* mypy clean — remove httpx from filestation, fix type annotations, List imports ([e74314f](https://github.com/by-openclaw/lib-synology-dsm/commit/e74314f41e3c3ff157b3ba64df63581bf4c5d409))
* redact hardcoded credentials, IPs; add pytest-cov 80% gate; migrate client to urllib ([120bac1](https://github.com/by-openclaw/lib-synology-dsm/commit/120bac11856793ebd93bc2f88cf155d9b151251b))
* remove httpx, redact all credentials/IPs, add pytest-cov 80% gate ([4788175](https://github.com/by-openclaw/lib-synology-dsm/commit/4788175d9e275c7a3bceaedf5f14853f3a349455))
* ruff lint — add missing os import, fix import order, remove unused imports ([c3d77a5](https://github.com/by-openclaw/lib-synology-dsm/commit/c3d77a51bc261749f4cda6c1ef6cbcc96ec3355f))
* share create uses shareinfo JSON; NFS uses correct API; add bash CRUD test script ([7831bcb](https://github.com/by-openclaw/lib-synology-dsm/commit/7831bcbbf44cd90725be269eb85b15fce515db93))
* **shares:** correct NFS API to SYNO.Core.FileServ.NFS.SharePrivilege (load/save); document name_org requirement for create ([591e015](https://github.com/by-openclaw/lib-synology-dsm/commit/591e015d19ce1079cf6c4a834a8dbe49003177ca))
* **shares:** full CRUD + user/group permissions + NFS via compound requests; fix share_name param for NFS SharePrivilege ([f9bdd64](https://github.com/by-openclaw/lib-synology-dsm/commit/f9bdd64f23bbe143e79d465d27c19c41815d271e))
* **shares:** use shareinfo JSON object for create (DSM 7.x requirement); add set_permission(), create_with_permissions() ([de1b7ad](https://github.com/by-openclaw/lib-synology-dsm/commit/de1b7ad980dcc08b7c557c1162f01a8c64e4f130))
* X-SYNO-TOKEN required for all write ops; group member uses set not member_set ([da18a43](https://github.com/by-openclaw/lib-synology-dsm/commit/da18a4343f5839e56faaaa3a2b5f32901f5d50ba))


### Documentation

* add CHANGELOG, CONTRIBUTING, CI workflow, API reference — complete to standard ([7de8684](https://github.com/by-openclaw/lib-synology-dsm/commit/7de868403b67ceb6b966c4438688debaefb9ea75))
* add compare links to CHANGELOG (v0.1.0..v0.7.0) ([2d9bfd5](https://github.com/by-openclaw/lib-synology-dsm/commit/2d9bfd58edd3f4fd0be39fd041d3724409ea618d))
* add confirmed DSM account permission requirements — administrators group mandatory; verified 2026-03-28 ([0c7e39a](https://github.com/by-openclaw/lib-synology-dsm/commit/0c7e39aa88e8f30d383b14a2d4b25cd5cdef7295))
* add feature coverage table, API references, CLAUDE.md; bump to v0.4.0 ([c555bcc](https://github.com/by-openclaw/lib-synology-dsm/commit/c555bccb21b115347cc5a6de868b167ee0f693d6))
* add hardening guide and lib capability summary ([90d8e84](https://github.com/by-openclaw/lib-synology-dsm/commit/90d8e84141239474680dc607fbe34d103c4e78a7))
* add validated share lifecycle reference script (yboujraf, 2026-03-28) ([d301e43](https://github.com/by-openclaw/lib-synology-dsm/commit/d301e435cf6a564ac43e32e43c14b819d2715d2d))
* AGENTS.md — add FileStation to module description ([d2e756b](https://github.com/by-openclaw/lib-synology-dsm/commit/d2e756b8c0abbd52187875cfb0ba30f593d9ef65))
* **claude:** add F12 DevTools debugging pattern + DSM API quirks discovered ([df29da1](https://github.com/by-openclaw/lib-synology-dsm/commit/df29da16eb25ceefd1feb41ac1dffab2037fa92e))
* project stats + doc-maintenance rule in AGENTS.md, docs/adr/ scaffold ([37a9b56](https://github.com/by-openclaw/lib-synology-dsm/commit/37a9b5618650b43a525919b2353dc347b7552b99))
* remove redundant API table from references.md; clarify CLAUDE.md blocked items + admin group decision ([da4b7d2](https://github.com/by-openclaw/lib-synology-dsm/commit/da4b7d2a520bb45f86a11f1fc9c9aeb256e6b0d2))
* sync CLAUDE.md + CHANGELOG — v0.6.0/0.6.1 FileStation, API gotchas, current state ([deb1f62](https://github.com/by-openclaw/lib-synology-dsm/commit/deb1f62bff9d54864ef1f61f56143bc5d3195be9))
* update feature-coverage — FileStation fully implemented (v0.6.1) ([6978c9e](https://github.com/by-openclaw/lib-synology-dsm/commit/6978c9e0ecf6b46feec0e639d95dc9e31b05390e))
* update README and CLAUDE.md to reflect working state and API quirks ([a686c9e](https://github.com/by-openclaw/lib-synology-dsm/commit/a686c9e2f2a6c087410e927e319cc6ba3145feb8))

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
