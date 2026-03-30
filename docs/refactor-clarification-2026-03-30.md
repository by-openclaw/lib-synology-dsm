# lib-synology-dsm — Refactoring Clarification & Prioritization

> **Date:** 2026-03-30
> **Last updated:** 2026-03-30 04:18 UTC
> **Status:** Tasks A–E complete. Pending: F–L (see section 8).
> **Tracking rule:** Rune updates this file immediately on any task completion or decision change. Save only — never committed unless explicitly requested by yboujraf.
> **Context:** This library is a nano-component of the BY-SYSTEMS PoC platform.
> It must be production-grade before the Ansible collection and orchestration layers can be built on top of it.
> For current state, manager status, and hard rules — see `CLAUDE.md`.

---

## 1. Gaps & Decisions

### 1.1 curl/bash scripts
Shell scripts in `tests/integration/curl/` are smoke tests, not a reusable library.

**Decision:** Keep as smoke tests. Purpose: validate payloads against the DSM API before developing new Python commands. No standalone bash lib.

### 1.2 Python lib — incomplete modules
3 modules exist as read-only stubs with no `ensure()`:

| Module | Status |
|---|---|
| `quota.py` | Read-only stub — no manager class |
| `storage.py` | Read-only stub — no manager class |
| `bandwidth.py` | Read-only stub — no manager class |

**Decision:** These need `ensure()` — Ansible playbooks will CRUD quota/storage/bandwidth. The Python lib must support the ensure pattern so Ansible modules can wrap them. Gap to fill before v1.0.

### 1.3 `FileStation.upload()` return dict inconsistency
Returns `{"skipped": bool}` instead of `{"changed": bool, "action": str}`. All other managers use the latter. **Must be normalized for v1.0.**

### 1.4 Return dict audit
Some managers use `changed`, others use `action` inconsistently. All manager methods must return `{"changed": bool, "action": str}`. **Needs full audit.**

### 1.5 Timeout & streaming
- Single `timeout=30` hardcoded in `client.py:69` — no per-operation, no configurable, no retry.
- `FileStationManager.upload()` reads entire file into memory before sending.
- **This needs its own ADR/issue** — too detailed for this doc. Key point: it's a v1.0 blocker.

### 1.6 `DSMClient` separation of concerns
`DSMClient` handles both auth session management AND HTTP transport. Should be split into `DSMSession` + `DSMTransport`. Not urgent pre-v1.0, but noted.

---

## 2. Repo Hygiene

### 2.1 Committed build artifacts — remove + gitignore
- `.mypy_cache/` (also contains stale httpx stubs from pre-v0.7.2)
- `htmlcov/`, `coverage.xml`, `.coverage`
- Possibly `.venv/` — verify if tracked

### 2.2 Scripts location
`tests/integration/curl/` mixes reference scripts with test infra. Should reusable scripts live in `scripts/`?

### 2.3 LICENSE
- Add individual author: `Copyright (c) 2026 BY-SYSTEMS — Youssef Boujraf`
- Add SPDX headers (`# SPDX-License-Identifier: MIT`) to all `.py` source files

### 2.4 Documentation cleanup
- `docs/api-reference.md` — keep as per-repo reference. Separation of concerns: each repo owns its own docs, accessible to anyone with repo access. A global doc risks access gaps.
- `docs/audits/` — archive to `docs/archive/` before release. Do not delete — historical audit records (6 files: overview, git workflow, security, python skeleton, src/docs/tests, PEP compliance). Move when v1.0 ships.
- `CONTRIBUTING.md` missing: how to run nox for local CI parity
- `docs/devcontainer-platform-tests.md` — verify still relevant

### 2.5 AI agent files
`AGENTS.md` and `CLAUDE.md` need audit to reflect v0.9.x state. No other agent files needed at this time.

---

## 3. Diagrams

### 3.1 Architecture diagram
`assets/diagrams/lib-architecture.puml` is stale (v0.7.x). Missing: quota, storage, bandwidth modules. FileStation partial.

**Action:** Regenerate to reflect v0.9.x. ASCII for README, PlantUML + PNG in `assets/`.

**Decision needed:** Class hierarchy only, or also data flow (request → DSMClient → API → response → ensure())?

### 3.2 Context diagram (new)
Does not exist yet.

**Decision needed:** Scope = lib ↔ DSM API only, or full orchestration context (lib ↔ Ansible ↔ NAS)?

---

## 4. Project Management

### 4.1 RAID
**Decision:** Per-repo. Separation of concerns — each repo should have its own RAID visible to those with repo access. A centralized RAID in `doc-platform-core` risks access gaps (not everyone has access to that repo) and mixes concerns across components.

### 4.2 Issue automation gaps
- Conventional commit footers (`Closes #N`) not used consistently — enforce in CONTRIBUTING.md + PR template
- No label enforcement on issues — add `.github/labels.yml` + labeler action
- GitHub Projects board not auto-populated — add `actions/add-to-project` workflow
- Issue templates missing pre-filled `label` field

---

## 5. Priority Matrix

| # | Topic | Priority | Effort | Blocker for v1.0? |
|---|---|---|---|---|
| 1.5 | Timeout + streaming upload | HIGH | Medium | YES |
| 1.3 | `FileStation.upload()` return dict | HIGH | Low | YES |
| 2.1 | Remove committed build artifacts | HIGH | Low | YES |
| 1.4 | Return dict audit — all managers consistent | HIGH | Low | YES |
| 2.3 | LICENSE author + SPDX headers | MEDIUM | Low | NO |
| 3.1 | Regenerate architecture diagram | MEDIUM | Low | NO |
| 3.2 | Context diagram (new) | MEDIUM | Low | NO |
| 4.2 | Issue automation | MEDIUM | Medium | NO |
| 1.2 | Quota/storage/bandwidth ensure() | HIGH | Medium | YES |
| 2.5 | Update AGENTS.md + CLAUDE.md | LOW | Low | NO |
| — | Ansible collection | LOW | High | NO (post v1.0) |

---

## 6. Decisions Log (confirmed 2026-03-30)

| # | Question | Decision |
|---|---|---|
| Q1 | Multi-language in this repo or separate repos? | **Separate repos.** Each lib is language-specific. Python for Ansible/file processing. Go/C++ for real-time. No same lib in multiple languages. |
| Q2 | curl/bash: standalone lib or smoke tests only? | **Smoke tests only.** Used to validate payloads before developing new Python commands. |
| Q3 | `docs/api-reference.md`: keep or remove? | **Keep, per-repo.** Separation of concerns — repo-scoped docs accessible to anyone with repo access. |
| Q4 | `docs/audits/`: archive or delete? | **Archive to `docs/archive/` at release.** Never delete — move when v1.0 ships. |
| Q5 | What defines v1.0.0? | All priority matrix blockers resolved + audits archived at release. |
| Q6 | Quota/storage/bandwidth: read-only or needs ensure()? | **Needs ensure().** Ansible playbooks will CRUD these — Python lib must support the pattern. |

---

---

## 7. Decision Log — Clarification Round 2 (2026-03-30 04:00–04:14 UTC)

| # | Topic | Decision | Decided by | Time |
|---|---|---|---|---|
| D-01 | storage.py ensure() semantics | Read-assert pattern. `state=present` → volume found = return info, not found = raise `DSMResourceNotFoundError`. `state=absent` → reports state, no write (API limitation). `dry_run` param kept for API consistency. | yboujraf | 04:11 UTC |
| D-02 | curl/bash scripts location | Keep in `tests/integration/curl/` — smoke tests only, not a reusable lib | yboujraf | 04:11 UTC |
| D-03 | Architecture diagram scope (3.1) | Full: class hierarchy + data flow + exception tree. PlantUML → Kroki → PNG in `assets/exports/` | yboujraf | 04:11 UTC |
| D-04 | Context diagram scope (3.2) | Full context: lib ↔ NAS ↔ Vault ↔ callers. Ansible collection shown as future/dashed. Same render pipeline. | yboujraf | 04:11 UTC |
| D-05 | storage.py — quota/bandwidth ensure() | `QuotaManager.ensure()` + `BandwidthManager.ensure()` = v1.0 blocker. `StorageManager` = read-only by design (no DSM write API for volumes). | yboujraf | 04:06 UTC |

---

## 8. Implementation Progress (live tracking)

> Updated by Rune as work completes. Team: check this section for current status.

| Task | Description | Status | Completed |
|---|---|---|---|
| A | `StorageManager.ensure()` read-assert + 5 unit tests | ✅ Done | 2026-03-30 04:15 UTC |
| B | Architecture diagram rewrite (lib-architecture.puml + PNG) | ✅ Done | 2026-03-30 04:15 UTC |
| C | Context diagram (lib-context.puml + PNG) — new | ✅ Done | 2026-03-30 04:15 UTC |
| D | Repo hygiene: .gitignore verified clean, no tracked artifacts | ✅ Done | 2026-03-30 04:15 UTC |
| E | Commit `3bad26d` pushed to main (228 tests passing) | ✅ Done | 2026-03-30 04:15 UTC |
| F | GitHub issues creation for all priority matrix items | ⏳ Pending E | — |
| G | RAID.md creation (per-repo, D-05 confirmed) | ⏳ Pending E | — |
| H | Update AGENTS.md + CLAUDE.md to v0.9.x state | ⏳ Backlog | — |
| I | LICENSE: add author + SPDX headers to all .py files | ⏳ Backlog | — |
| J1 | `QuotaManager.ensure()` + `set_user/group_quota()` | ✅ Done | 2026-03-30 04:47 UTC |
| J2 | `BandwidthManager.ensure()` | ⏳ Pending F12 capture (bandwidth set payload) | — |
| K | Timeout: per-operation defaults + streaming upload | ⏳ Backlog (v1.0 blocker) | — |
| L | Return dict audit — all managers consistent | ⏳ Backlog (v1.0 blocker) | — |

---

*This file is the team's live working doc. Rune updates section 8 as tasks complete. Do not commit until explicitly requested.*
