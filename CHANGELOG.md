# Changelog

## [0.11.0](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.10.1...v0.11.0) (2026-10-03)


### Features

* ADR-0007 compliance — upload return dict, configurable timeout, update/disable return dict, smoke tests ([033ba2c](https://github.com/by-openclaw/lib-synology-dsm/commit/033ba2ced80d1fadfab512b9c6abc5da6322cf93))
* **share-permissions:** SharePermissionManager with full ACL lifecycle + ensure() ([6bb30b4](https://github.com/by-openclaw/lib-synology-dsm/commit/6bb30b4df88da2a66473385153a8fa28ce5688e2))
* **system:** SystemManager with get_info() + ensure() for NetBox fact gathering ([b9ae4a4](https://github.com/by-openclaw/lib-synology-dsm/commit/b9ae4a480d58df27c0df0a4db800533aa41235b3))
* **v2:** add synology_dsm_v2 foundation — client, base, user manager, exceptions ([38ede5f](https://github.com/by-openclaw/lib-synology-dsm/commit/38ede5faad2d6c4c31de1f6ed45cc7f3bced9165))
* **v2:** CoreFileServNFSManager — SYNO.Core.FileServ.NFS ([ed214d8](https://github.com/by-openclaw/lib-synology-dsm/commit/ed214d859ed0f8e307eb22762e11b8821ef1bc0b))
* **v2:** CoreGroupManager — SYNO.Core.Group ([80136cb](https://github.com/by-openclaw/lib-synology-dsm/commit/80136cbb393cfefebf38a1ca1d0c546d496d3472))
* **v2:** CoreShareManager — SYNO.Core.Share ([e484d29](https://github.com/by-openclaw/lib-synology-dsm/commit/e484d290e137aacc07bb6288f02513ea33b6a9d0))
* **v2:** export all 5 managers + integration tests ([c577c1e](https://github.com/by-openclaw/lib-synology-dsm/commit/c577c1ed318180842d6a379a5b6cc43e0742ee43))
* **v2:** FileStationManager — SYNO.FileStation ([912d64d](https://github.com/by-openclaw/lib-synology-dsm/commit/912d64d23ec7fdfc186f1586971f0cbd3d52d112))


### Bug Fixes

* **agents:** link to doc-platform-core for agent contract files ([5f1134c](https://github.com/by-openclaw/lib-synology-dsm/commit/5f1134c6d4f3bdb2fe39931cdc7167e3d672d116))
* **agents:** remove unreachable OPERATING-STANDARD.md link ([2d8752a](https://github.com/by-openclaw/lib-synology-dsm/commit/2d8752ae7ddc5d91265138e262eeb0791043d158))
* **agents:** restore OPERATING-STANDARD reference as plain text ([f10d3f5](https://github.com/by-openclaw/lib-synology-dsm/commit/f10d3f5e056d463c5662cc8252b6d248693d6168))
* **ci:** align coverage gate — 80% in pyproject, README, PR template ([4a6300f](https://github.com/by-openclaw/lib-synology-dsm/commit/4a6300f9266e0713dad62b6c273ef8a3b72cebb5))
* **ci:** annotate the one Bandit finding, with the reason it cannot be exploited ([2e2b9db](https://github.com/by-openclaw/lib-synology-dsm/commit/2e2b9dbedc47ee712c234e0ea4816d63ba9ac170))
* **ci:** one ruff version, so a red check means something again ([6c023f2](https://github.com/by-openclaw/lib-synology-dsm/commit/6c023f2e6804015b2edf3a8da8e3f62c4fc58eeb))
* **ci:** one ruff version, so a red check means something again ([038eb30](https://github.com/by-openclaw/lib-synology-dsm/commit/038eb3016e75f24bf2c55bacbe2c6bc742ddb464)), closes [#57](https://github.com/by-openclaw/lib-synology-dsm/issues/57)
* **ci:** ruff format v1 files; exclude v2 WIP dirs from CI scope; add PROJECT_TOKEN ([1f7299c](https://github.com/by-openclaw/lib-synology-dsm/commit/1f7299cff198aa8f5a4db1987a9f37f9db8d838c))
* **client:** correct login/logout to use auth.cgi + SYNO.API.Auth v7 per official Synology KB ([b54c919](https://github.com/by-openclaw/lib-synology-dsm/commit/b54c919e724a0461ab283f859f757dc3f3703501))
* **exceptions:** align error map to DSM spec — add DSMInvalidParameterError, DSMInvalidOperationError, fix DSMNotFoundError code 408→404 ([15a10b1](https://github.com/by-openclaw/lib-synology-dsm/commit/15a10b18c0b603c5632814390c647b72155e2c68))
* **filestation:** download returns {changed,action}, upload/download use client timeout; update CLAUDE.md; add audit files 17-18 ([c7ca01e](https://github.com/by-openclaw/lib-synology-dsm/commit/c7ca01eb78c1c5d16f11bfd9d0c0b62c38f99092))
* **v2:** integration test fixes — group desc DSM quirk, Share.set 2FA skip, FileStation session ([3c2213c](https://github.com/by-openclaw/lib-synology-dsm/commit/3c2213c42a8da21d5bd07ac7315254bfe3f68889))
* **v2:** production-readiness fixes + PR template v2 paths ([1d5dff9](https://github.com/by-openclaw/lib-synology-dsm/commit/1d5dff97215bafe6ad2c42432eced0880a6e0acf))
* **v2:** suppress Bandit B310 on FileStation urlopen — URL from trusted config, not user input ([79d28ab](https://github.com/by-openclaw/lib-synology-dsm/commit/79d28ab2767d89ea466ac920f51591ea9420943a))


### Documentation

* add OPERATING-STANDARD.md + update feature-coverage.md ([d40400e](https://github.com/by-openclaw/lib-synology-dsm/commit/d40400e96b557d3144d5bd45741e9ee4742b7096))
* add OPERATING-STANDARD.md + update feature-coverage.md with n4s4 gap analysis ([7c76025](https://github.com/by-openclaw/lib-synology-dsm/commit/7c760254ad72295fc0c6ecaa513c3b9af4eaaeb2))
* **adr:** add compliance sections to ADR-0001 through 0009 ([fd3cfbb](https://github.com/by-openclaw/lib-synology-dsm/commit/fd3cfbbe6deb472eb463f1f9c2de86ff38f79663))
* **adr:** ADR-0008 method naming convention ([5e5e55f](https://github.com/by-openclaw/lib-synology-dsm/commit/5e5e55feb40b6ada015f18b2244a93b81fc01967))
* **agent:** refresh env tier reference for Opus ([5dd32f3](https://github.com/by-openclaw/lib-synology-dsm/commit/5dd32f35635ac2275f97736b664085be8982a607))
* align agent files with sprint ADRs (Block 3) ([6911963](https://github.com/by-openclaw/lib-synology-dsm/commit/69119639e9f2bcca207f8bac9fee0fce6a538460))
* **audit:** review checklist 2026-03-31 ([540b7bd](https://github.com/by-openclaw/lib-synology-dsm/commit/540b7bdc01ac77980de68c2f72ad4bf8ee1c3efe))
* **changelog:** consolidate to single release-please format ([edf3fc2](https://github.com/by-openclaw/lib-synology-dsm/commit/edf3fc2f67058ea2f0e26e3556f0cbfee3590d4c))
* CLAUDE.md references OPERATING-STANDARD.md ([c997a1e](https://github.com/by-openclaw/lib-synology-dsm/commit/c997a1eea637c8d9fe3c27f0d43c15c3297ea7d6))
* **claude:** reflect CI scope fix, v2 WIP dirs, ADR count, test count ([1bcc470](https://github.com/by-openclaw/lib-synology-dsm/commit/1bcc470cd888918ad6b740a72f3a1b9cdde00737))
* **feature-coverage:** full rewrite — all 9 managers, correct status, NetBox priority, SSH/CopyMove in TODO ([4a95698](https://github.com/by-openclaw/lib-synology-dsm/commit/4a95698956db2c280f731037ff7f78b449eba229))
* **lib:** api-versions.md — verified against v1 source, 9 managers ([01c3e82](https://github.com/by-openclaw/lib-synology-dsm/commit/01c3e82a9874a0cd36ec0b5cfed5e540915949dc))
* NAS firewall port inventory + 2FA API compatibility research ([2372e22](https://github.com/by-openclaw/lib-synology-dsm/commit/2372e22113eeadf699ee9027b825b01fdbf9bea8))
* pre-sprint baseline — ADR-0009, v2 design, CI proposal, integration tests ([41512f3](https://github.com/by-openclaw/lib-synology-dsm/commit/41512f30a27c0442d6a783a9a9d085f9fb021667))
* update feature-coverage.md + CHANGELOG.md for SharePermissionManager + SystemManager ([6c8992b](https://github.com/by-openclaw/lib-synology-dsm/commit/6c8992b11b1bf3045ab34f352d284e031ba347a4))
* **v2:** lock FileStation multi-API decision — Option A (self._client.request direct) ([d0e01e6](https://github.com/by-openclaw/lib-synology-dsm/commit/d0e01e65b351cda0b5aa5cbbbb66e9508ee0e49b))
* **v2:** update coverage and design doc ([bd9afb9](https://github.com/by-openclaw/lib-synology-dsm/commit/bd9afb9b9ba3bfcd943bdc078060884921106135))

## [Unreleased]

### Features

* **share-permissions:** SharePermissionManager with full ACL lifecycle — list, set, set_bulk, ensure() with state=present/absent and dry_run support
* **system:** SystemManager with get_info() + ensure() for NetBox fact gathering — SYNO.DSM.Info primary, SYNO.Core.System fallback

### Tests

* Split integration tests into per-manager files (11 files) for maintainability
* 100% unit coverage for SharePermissionManager (33 tests) and SystemManager (12 tests)
* Integration tests for SharePermissionManager (8 tests) and SystemManager (5 tests)

## [0.10.3](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.10.1...v0.10.3) (2026-03-31)

### Bug Fixes

* `login()` corrected to use `/webapi/auth.cgi` (was incorrectly using `entry.cgi`) per official DSM Login Web API Guide
* `login()` API version bumped from `6` to `7` (current max per Synology KB)
* `logout()` API version bumped from `1` to `7`
* `logout()` now includes `session` parameter (required by spec)
* `DSMNotFoundError.code` corrected from 408 to 404 per official DSM API spec
* Error map in `client.py` aligned to official error-handling guide

### Features

* `DSMInvalidParameterError` — new exception for parameter errors (codes 100, 101, 102, 120, 1001, 1009, 1010)
* `DSMInvalidOperationError` — new exception for invalid operation state (code 117)
* **smoke:** smoke test suite (`tests/smoke/`) — import and instantiation checks
* **bandwidth:** full read+write+ensure+dry_run for user and group bandwidth shaping
* **trafficcontrol:** new TrafficControlManager — load, save, add_rule, remove_rule, clear_rules, ensure_rule

### Fixed

* **filestation:** `upload()` now returns ADR-0007 compliant `{"changed": bool, "action": str}` dict
* **client:** `DSMClient` accepts configurable `timeout` parameter (default 30s)
* **users:** `UserManager.update()` returns `{"changed": True, "action": "updated", "target": name}`
* **users:** `UserManager.disable()` returns `{"changed": True, "action": "disabled", "target": name}`
* **groups:** `GroupManager.update()` returns `{"changed": True, "action": "updated", "target": name}`
* **shares:** `ShareManager.update()` returns `{"changed": True, "action": "updated", "target": name}`

### Tests

* 5 new unit tests for login/logout auth flow
* 12 new unit tests for all newly mapped error codes

## [0.10.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.10.0...v0.10.1) (2026-03-30)

### Bug Fixes

* correct pull_request trigger in project-board-sync workflow ([49ca818](https://github.com/by-openclaw/lib-synology-dsm/commit/49ca81847184812cbdc74c5afec14711051396b0))

### Documentation

* add ADR-0004/0005/0007, fix ADR-0001/0002/0003, add RAID.md, update SECURITY.md ([62c0749](https://github.com/by-openclaw/lib-synology-dsm/commit/62c074925ef9cd60bb34c3933de5ae4d9ef151ef))
* apply full Tier 1 audit remediation — CLAUDE.md, AGENTS.md, CONTRIBUTING.md, ADRs ([20e143f](https://github.com/by-openclaw/lib-synology-dsm/commit/20e143f65891721d07f4a4424054b31ad0adf711))

## [0.10.0](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.3...v0.10.0) (2026-03-30)

### Features

* BandwidthManager write ops + TrafficControlManager ([a46908e](https://github.com/by-openclaw/lib-synology-dsm/commit/a46908e0e75ade1ebfa02c181e2b25ee09ecd5ad))
* **quota:** ensure() + set_user/group_quota with MB-native interface ([7cb58f2](https://github.com/by-openclaw/lib-synology-dsm/commit/7cb58f2b852ab12db046e0dda996d69e8aa70e2b))
* storage ensure() read-assert pattern + diagrams + repo hygiene ([3bad26d](https://github.com/by-openclaw/lib-synology-dsm/commit/3bad26d13d5a5cba183b6c5b06b87e7f2b8a5dbd))

### Bug Fixes

* auto-update version badge in README via release-please extra-files ([2dc0395](https://github.com/by-openclaw/lib-synology-dsm/commit/2dc03958267901b1cd861b5dbde6bffb08df8cf8))

## [0.9.3](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.2...v0.9.3) (2026-03-30)

### Bug Fixes

* remove type annotation from __version__ so release-please can update it ([c5b9812](https://github.com/by-openclaw/lib-synology-dsm/commit/c5b981207e8034816bdfdb5ad2c4058b50667810))

## [0.9.2](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.1...v0.9.2) (2026-03-30)

### Bug Fixes

* **devcontainer:** drop root user — use vscode + venv ([187f18d](https://github.com/by-openclaw/lib-synology-dsm/commit/187f18d1cd5569bbda7de10f0a79da96e62a10d3))

## [0.9.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.9.0...v0.9.1) (2026-03-30)

### Bug Fixes

* **ci:** remove release-type from workflow — use manifest mode only ([7383e96](https://github.com/by-openclaw/lib-synology-dsm/commit/7383e96c05903cec661a38d53517a18150c76665))
* **types:** resolve all 27 mypy errors across 7 files ([46e7dfe](https://github.com/by-openclaw/lib-synology-dsm/commit/46e7dfe5d1bb50f5aad2a64d19850c8770a3d67a))

## [0.9.0](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.8.2...v0.9.0) (2026-03-29)

### Features

* StorageManager, QuotaManager, BandwidthManager, SharePermissions ([4ffaaa6](https://github.com/by-openclaw/lib-synology-dsm/commit/4ffaaa6defd3504c24e024190012ecc92a202664))

## [0.8.2](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.8.1...v0.8.2) (2026-03-29)

### Bug Fixes

* third audit pass — all remaining findings resolved ([6760021](https://github.com/by-openclaw/lib-synology-dsm/commit/67600215a7a5572c85ed199fd25d5346a4964a85))

## [0.8.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.8.0...v0.8.1) (2026-03-29)

### Bug Fixes

* enforce consistent return pattern — all methods return {changed, action} ([b6b1690](https://github.com/by-openclaw/lib-synology-dsm/commit/b6b16902a550b5aa12a07f7afb20231335e7f261))
* group member_list DSM firmware limitation + full ensure() integration test ([f97cdc1](https://github.com/by-openclaw/lib-synology-dsm/commit/f97cdc1e93272a13a1e2cc59b3d5b1e679be20e0))

## [0.8.0](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.3...v0.8.0) (2026-03-29)

### Features

* NFSManager ensure(), FileStation ensure(), Vault cleanup ([23c8a6c](https://github.com/by-openclaw/lib-synology-dsm/commit/23c8a6c4bbb3c69b591365c4451b0f57fa82afad))
* pre-commit hooks — detect-secrets + ruff + hygiene checks ([85acf39](https://github.com/by-openclaw/lib-synology-dsm/commit/85acf39a64dda81167976c73706001af7151e46e))

## [0.7.3](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.2...v0.7.3) (2026-03-29)

### Bug Fixes

* 17-point audit — all items addressed ([9777388](https://github.com/by-openclaw/lib-synology-dsm/commit/9777388211bebf799bc03e2cdaa218ea47313281))

## [0.7.2](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.1...v0.7.2) (2026-03-29)

### Bug Fixes

* complete credential redaction in test_live_nas.py; add .env.example for integration tests ([101baf7](https://github.com/by-openclaw/lib-synology-dsm/commit/101baf756449696d8f6005d0b2f683196a99076d))

## [0.7.1](https://github.com/by-openclaw/lib-synology-dsm/compare/v0.7.0...v0.7.1) (2026-03-29)

### Bug Fixes

* post-audit hardening — urllib migration, credential redaction, CI green ([c48f61b](https://github.com/by-openclaw/lib-synology-dsm/commit/c48f61b23d081f217cb0cdedcb9dcc62c8f24d93))

## [0.7.0](https://github.com/by-openclaw/lib-synology-dsm/releases/tag/v0.7.0) (2026-03-29)

### Features

* Initial release — DSMClient, UserManager, GroupManager, ShareManager, NFSManager, FileStationManager
* ensure() idempotency with diff detection and dry_run support
* Typed exception hierarchy — DSMError, DSMAuthError, DSMPermissionError, DSMSessionError, DSMAPIError
* Credential providers — EnvCredentialProvider, VaultCredentialProvider
* Full unit test coverage (345 tests)
