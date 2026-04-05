# Changelog

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
