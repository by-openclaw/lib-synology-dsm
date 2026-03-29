# Changelog

## [0.9.0](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.8.2...v0.9.0) (2026-03-29)


### Features

* v0.9.0 — StorageManager, QuotaManager, BandwidthManager, SharePermissions ([4ffaaa6](https://github.com/by-openclaw/lib-synology-dsm/commit/4ffaaa6defd3504c24e024190012ecc92a202664))


### Bug Fixes

* fourth audit pass — module docstring, test counts, noxfile ([9d6bedb](https://github.com/by-openclaw/lib-synology-dsm/commit/9d6bedb58c17ae3bd5f38b8950ca173861642e5c))
* sync __version__ and commitizen to 0.8.2 ([ad9f89e](https://github.com/by-openclaw/lib-synology-dsm/commit/ad9f89ebde3f77a604632dd8cc6c67ef346a38ee))

## [0.8.2](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.8.1...v0.8.2) (2026-03-29)


### Bug Fixes

* __enter__ docstring + remove last os.environ from README ([19fb6bf](https://github.com/by-openclaw/lib-synology-dsm/commit/19fb6bf130c26b74c3076725dbc3ab8ffd4ed265))
* sync __version__ to 0.8.1 after release-please merge ([af54471](https://github.com/by-openclaw/lib-synology-dsm/commit/af544718004eb63a27ffad6efeb0eed8f269d862))
* third audit pass — all remaining findings resolved ([6760021](https://github.com/by-openclaw/lib-synology-dsm/commit/67600215a7a5572c85ed199fd25d5346a4964a85))
* update 02-groups.sh to use SYNO.Core.Group.Member add/list APIs ([f1edda1](https://github.com/by-openclaw/lib-synology-dsm/commit/f1edda14b09351f38b3678e0f52d68db913bbdc0))
* use correct DSM Group.Member API — discovered via DevTools F12 ([149b713](https://github.com/by-openclaw/lib-synology-dsm/commit/149b713ba536efc651cc7e1ace54210d70722583))

## [0.8.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.8.0...v0.8.1) (2026-03-29)


### Bug Fixes

* apply compliance audit — typing, docstrings, dead code, packaging ([7ab1f79](https://github.com/by-openclaw/lib-synology-dsm/commit/7ab1f79fa9355086d9083b55412845594de6d818))
* enforce consistent return pattern — all methods return {changed, action} ([b6b1690](https://github.com/by-openclaw/lib-synology-dsm/commit/b6b16902a550b5aa12a07f7afb20231335e7f261))
* group member_list DSM firmware limitation + full ensure() integration test ([f97cdc1](https://github.com/by-openclaw/lib-synology-dsm/commit/f97cdc1e93272a13a1e2cc59b3d5b1e679be20e0))
* integration test — 4 bugs fixed, 30/31 passing ([8c68bf5](https://github.com/by-openclaw/lib-synology-dsm/commit/8c68bf5d0f203dcb795ae2eec14e1bf0f0dc32c8))
* list_members — proper fallback chain + document DSM 7.1.x member_list bug ([6a4cced](https://github.com/by-openclaw/lib-synology-dsm/commit/6a4cced48b94a0c0431197080c518b15580ea64f))
* packaging, CI, pytest integration suite — second audit pass ([df6bdcb](https://github.com/by-openclaw/lib-synology-dsm/commit/df6bdcba7612c853c9f205a1dacd811f8ebac809))
* upgrade DSM to 7.2.x — tracked in platform-setup[#54](https://github.com/by-openclaw/lib-synology-dsm/issues/54) ([6a4cced](https://github.com/by-openclaw/lib-synology-dsm/commit/6a4cced48b94a0c0431197080c518b15580ea64f))


### Documentation

* badges, dev container ext, false positive walkthrough ([0cfa53e](https://github.com/by-openclaw/lib-synology-dsm/commit/0cfa53efe02220adcfea5607543d7438fe32c7d3))
* clarify pre-commit hooks table — LFS pointer behavior, binary file handling ([6018fd7](https://github.com/by-openclaw/lib-synology-dsm/commit/6018fd739c469f1fb3893b5bbc8ebecbec848577))
* README — explicit dev container setup + pre-commit hooks section ([8187a2d](https://github.com/by-openclaw/lib-synology-dsm/commit/8187a2d4745b7120795b2e580c58bbcc104f2fc6))
* update CLAUDE.md + AGENTS.md to v0.8.0 state — 0 open issues ([8d9d3b1](https://github.com/by-openclaw/lib-synology-dsm/commit/8d9d3b11adbd66dcc76398fa92eb92f31653041e))

## [0.8.0](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.3...v0.8.0) (2026-03-29)


### Features

* close issues [#5](https://github.com/by-openclaw/lib-synology-dsm/issues/5) [#6](https://github.com/by-openclaw/lib-synology-dsm/issues/6) [#7](https://github.com/by-openclaw/lib-synology-dsm/issues/7) — NFSManager ensure(), FileStation ensure(), Vault cleanup ([23c8a6c](https://github.com/by-openclaw/lib-synology-dsm/commit/23c8a6c4bbb3c69b591365c4451b0f57fa82afad))
* pre-commit hooks — detect-secrets + ruff + hygiene checks ([85acf39](https://github.com/by-openclaw/lib-synology-dsm/commit/85acf39a64dda81167976c73706001af7151e46e))

## [0.7.3](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.2...v0.7.3) (2026-03-29)


### Bug Fixes

* 17-point audit — all items addressed ([9777388](https://github.com/by-openclaw/lib-synology-dsm/commit/9777388211bebf799bc03e2cdaa218ea47313281))

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
