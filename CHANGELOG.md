# Changelog

## [Unreleased]

### Features

* **bandwidth:** full read+write+ensure+dry_run — set_user, set_group, ensure_user, ensure_group, disable_user, disable_group
* **trafficcontrol:** new TrafficControlManager — load, save, add_rule, remove_rule, clear_rules, ensure_rule with idempotent pattern

## [0.9.3](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.2...v0.9.3) (2026-03-30)


### Bug Fixes

* remove type annotation from __version__ so release-please can update it ([c5b9812](https://github.com/by-openclaw/lib-synology-dsm/commit/c5b981207e8034816bdfdb5ad2c4058b50667810))

## [0.9.2](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.1...v0.9.2) (2026-03-30)


### Bug Fixes

* **devcontainer:** drop root user — use vscode + venv ([187f18d](https://github.com/by-openclaw/lib-synology-dsm/commit/187f18d1cd5569bbda7de10f0a79da96e62a10d3))

## [0.9.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.0...v0.9.1) (2026-03-30)


### Bug Fixes

* **ci:** remove release-type from workflow — use manifest mode only ([7383e96](https://github.com/by-openclaw/lib-synology-dsm/commit/7383e96c05903cec661a38d53517a18150c76665))
* **devcontainer:** add container extras group, exclude pre-commit ([94da4f6](https://github.com/by-openclaw/lib-synology-dsm/commit/94da4f68cec85e7fc33f25a3cc15e87fc2ae3190))
* **devcontainer:** auto-create .env.local from example if missing ([a4fd302](https://github.com/by-openclaw/lib-synology-dsm/commit/a4fd3025bb18a8ff4ac501f0ea6c45e351afee51))
* **devcontainer:** drop --network=host (no-op on Docker Desktop), fix \r line endings ([1116516](https://github.com/by-openclaw/lib-synology-dsm/commit/11165162e81bbd51e6802e536a98e6da72711eb4))
* **devcontainer:** load credentials via dotenv in conftest, not --env-file ([aa09dbb](https://github.com/by-openclaw/lib-synology-dsm/commit/aa09dbb0575320f075c270ec9db8d07e31fade92))
* **devcontainer:** pip install --user instead of sudo pip ([0837f2c](https://github.com/by-openclaw/lib-synology-dsm/commit/0837f2c46abc7afaee25ee8e810b87aa87ac5fb1))
* **devcontainer:** remove pre-commit install from postCreateCommand ([33f760e](https://github.com/by-openclaw/lib-synology-dsm/commit/33f760e6fbcd57bd0a78d45f811df191f5551551))
* **devcontainer:** remove remoteEnv, clarify integration tests run outside container ([baea464](https://github.com/by-openclaw/lib-synology-dsm/commit/baea464f985bed27d523d509a9ac0f3dc364479d))
* **devcontainer:** remove trailing comma (invalid JSON) ([7d35b12](https://github.com/by-openclaw/lib-synology-dsm/commit/7d35b1222cd8d014faa726ac47c85be59f484bc2))
* **devcontainer:** replace Windows env vars with gitignored .env.local file ([8d31d5b](https://github.com/by-openclaw/lib-synology-dsm/commit/8d31d5bce7028d559e03e843fe0bc064411e252f))
* **devcontainer:** set remoteUser=root to resolve pip permission errors ([d0713ff](https://github.com/by-openclaw/lib-synology-dsm/commit/d0713ff6b1df012ee7c16f674b3907d5f43f9aed))
* **devcontainer:** single .env file for native and container ([4cb037d](https://github.com/by-openclaw/lib-synology-dsm/commit/4cb037dc7c46a21d0ab0e0cb0bfd65046a80ff4c))
* **devcontainer:** sudo pip to fix site-packages not writable warning ([8acfc72](https://github.com/by-openclaw/lib-synology-dsm/commit/8acfc72d2a33bcfe28e4d856c9879243e8f3a69d))
* **devcontainer:** WSL2 mirrored networking for LAN access on Windows ([b90e701](https://github.com/by-openclaw/lib-synology-dsm/commit/b90e701736392a23a0d7dceab2396cb5dea042d5)), closes [#24](https://github.com/by-openclaw/lib-synology-dsm/issues/24)
* **docs:** robust .env loader — strip inline comments before xargs ([03d0fe2](https://github.com/by-openclaw/lib-synology-dsm/commit/03d0fe2be4cc82b1feb3bec4047f309d720885a6))
* **env:** remove duplicate and unused vars from .env.example ([7438d94](https://github.com/by-openclaw/lib-synology-dsm/commit/7438d94a8cb43db9583f3cab52350e10a46387a6))
* **integration:** handle empty NAS_PORT env var gracefully ([6a5ae98](https://github.com/by-openclaw/lib-synology-dsm/commit/6a5ae98cac27dd2e44e631784c61538bcb563728))
* **types:** resolve all 27 mypy errors across 7 files ([46e7dfe](https://github.com/by-openclaw/lib-synology-dsm/commit/46e7dfe5d1bb50f5aad2a64d19850c8770a3d67a))


### Documentation

* add architecture diagram + fix .env.example inline comments ([69b4fb4](https://github.com/by-openclaw/lib-synology-dsm/commit/69b4fb4540b3860c2a80f88c145d85827417d046))
* add docs/audits/ folder (00-05) — audit evidence committed to repo ([34e3348](https://github.com/by-openclaw/lib-synology-dsm/commit/34e33485ccde84512fd0297f95b6b1da6a87b720))
* add HARD RULES block to CLAUDE.md + AGENTS.md, sync current state to v0.9.0 ([c507d1f](https://github.com/by-openclaw/lib-synology-dsm/commit/c507d1f7032b883b29f37f2b0029e8d4e95ab35f))
* add version badge + fix Windows native setup instructions ([95d92c0](https://github.com/by-openclaw/lib-synology-dsm/commit/95d92c0c9d79af41439b3fc0f93ce0b91642a09f))
* **contributing:** clarify Path A vs B, unit vs integration tests, .env context ([cf35c07](https://github.com/by-openclaw/lib-synology-dsm/commit/cf35c07f6b3cda6f731846f359ba911f502828bb))
* **contributing:** expand dev container setup — Docker Desktop settings table + screenshot ([401e4ff](https://github.com/by-openclaw/lib-synology-dsm/commit/401e4ff502f683c2382392283fa898add86dcacb))
* **contributing:** fix Windows Git Bash Python setup ([4cc213c](https://github.com/by-openclaw/lib-synology-dsm/commit/4cc213c657ad9a53d24ae37ef51b626d4336970a))
* **contributing:** rewrite Path A/B with exact validated steps ([4cccd56](https://github.com/by-openclaw/lib-synology-dsm/commit/4cccd56585ea61a1879d277d3e0ef7b40d6bf886))
* **contributing:** rewrite Windows setup — clean 5-step guide for Git Bash ([6bf2f23](https://github.com/by-openclaw/lib-synology-dsm/commit/6bf2f236127006396d951c96ff5c9d6a4b551bf7))
* replace Codecov badge with static 100% badge, expand Testing section ([f5a4a94](https://github.com/by-openclaw/lib-synology-dsm/commit/f5a4a94646af3ce3099697313ece35b312353624))
* update dev container setup — terminal access, rebuild steps, pre-commit clarification ([8c529b6](https://github.com/by-openclaw/lib-synology-dsm/commit/8c529b610e0ef64b5b450443c1c95aa083a636d1))

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
