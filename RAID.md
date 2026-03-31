# RAID.md — lib-synology-dsm

> Scope: repo-level risks, issues, and dependencies.
> Platform-wide items: doc-platform-core/docs/raid.md
> Rule: if it affects this repo only → here. If it crosses repos → platform RAID.

---

## Risks

| ID | Risk | Impact | Likelihood | Mitigation | Status |
|---|---|---|---|---|---|
| R-001 | verify_ssl=False default — TLS not validated | HIGH | LOW | Pending platform TLS/cert strategy decision | OPEN |
| R-002 | mypy 27 errors — type safety gaps | MEDIUM | HIGH | Fix in progress — v1.0 blocker | OPEN |

## Issues

| ID | Issue | Priority | Status | GitHub |
|---|---|---|---|---|
| I-001 | FileStation.upload() returns {"skipped"} — violates return dict contract (ADR-0007) | HIGH | OPEN | — |
| I-002 | client.py timeout hardcoded at 30s — no per-op timeout, no streaming | HIGH | OPEN | — |

## Actions

| ID | Action | Owner | Due | Status |
|---|---|---|---|---|
| A-001 | Fix FileStation.upload() return dict | @yboujraf | v1.0 | OPEN |
| A-002 | Implement per-op timeout in client.py | @yboujraf | v1.0 | OPEN |
| A-003 | Fix mypy 27 errors | @yboujraf | v1.0 | OPEN |

| R-003 | Service account `rune-api` and group `svc-automation` do not follow ADR-0010 naming (`svc-{function}-{env}`) | MEDIUM | HIGH | Rename when Authentik (Layer 3) deployed. Document as known gap. | OPEN |
| R-004 | CLAUDE.md/AGENTS.md did not reference ADR-0010/ADR-0012 | LOW | HIGH | Fixed in sprint Block 3 | IN PROGRESS |

## Dependencies

| ID | Dependency | On | Blocks | Status |
|---|---|---|---|---|
| D-001 | TLS strategy decision | Platform cert/DNS (doc-platform-core) | verify_ssl fix | OPEN |
| D-002 | Vault deployment | infra-terraform-proxmox | VaultCredentialProvider Phase 2 | OPEN |
