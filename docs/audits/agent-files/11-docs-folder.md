# Audit: docs/ Folder

> **Scope:** `lib-synology-dsm/docs/` — all documentation files
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — stale files, archive candidates, ownership gaps

---

## Inventory

| File | Purpose | Status |
|---|---|---|
| `docs/adr/README.md` | ADR index | Current |
| `docs/adr/0001-urllib-over-httpx.md` | ADR: stdlib urllib | Current |
| `docs/adr/0002-ensure-pattern.md` | ADR: idempotent ensure() | Current |
| `docs/adr/0003-credential-provider-hierarchy.md` | ADR: credential providers | Current |
| `docs/ansible-roadmap.md` | Ansible collection plan | Current (Phase 2, deferred) |
| `docs/api-reference.md` | Method signatures and usage | **Needs update** — missing newer managers |
| `docs/api-versions.md` | Tested API version table | **Verify** — may lag behind code |
| `docs/credentials.md` | Credential provider docs | Current |
| `docs/devcontainer-platform-tests.md` | Dev container testing notes | **Verify** — may be stale |
| `docs/feature-coverage.md` | Feature matrix (implemented vs planned) | **Needs update** — verify newer managers reflected |
| `docs/hardening.md` | DSM account security guide | Current (see audit 09) |
| `docs/lib-summary.md` | Library overview | **Redundant?** — overlaps README |
| `docs/licenses.md` | Dependency license inventory | Current |
| `docs/references.md` | External links and resources | **Verify** — may have dead links |
| `docs/refactor-clarification-2026-03-30.md` | Refactor decisions + priority matrix | Current (live working doc) |
| `docs/release-process.md` | Release workflow docs | **Redundant?** — CONTRIBUTING.md covers release |
| `docs/audits/` | Historical audit snapshots (6 files) | **Archive candidate** — move to docs/archive/ at v1.0 |
| `docs/audits/agent-files/` | This audit set | Active |

---

## Issues by category

### Redundancy

| File | Overlaps with | Recommendation |
|---|---|---|
| `docs/lib-summary.md` | README.md | **Verify** — if it adds nothing beyond README, archive it |
| `docs/release-process.md` | CONTRIBUTING.md release section | **Verify** — if CONTRIBUTING.md covers the same, archive it. If it has extra detail (Release Please config), keep and reference from CONTRIBUTING.md |

### Staleness risk

| File | Risk | Action |
|---|---|---|
| `docs/api-reference.md` | Decision Q3: keep per-repo. But it must reflect all 10 managers. | Update to include QuotaManager, BandwidthManager, StorageManager, TrafficControlManager |
| `docs/api-versions.md` | May not include newer API endpoints used by quota/bandwidth/traffic | Verify against current code |
| `docs/feature-coverage.md` | Should reflect all managers + ensure() status | Cross-check with CLAUDE.md state table |
| `docs/devcontainer-platform-tests.md` | Unclear if still relevant post-v0.9.x | Read and decide: archive or update |
| `docs/references.md` | External links may be dead | Check all URLs |

### Archive candidates (confirmed by decision Q4)

Move to `docs/archive/` at v1.0 release:
- `docs/audits/00-overview.md` through `docs/audits/05-pep-compliance.md` (6 historical audit files)
- Any file confirmed redundant after verification above

---

## Missing

### M-1: No ADR for per-repo RAID decision

Decision D-06 (RAID per-repo, not centralized) was confirmed 2026-03-30 but has no ADR. This is an architectural decision.

**Action:** Create `docs/adr/0004-per-repo-raid.md`

### M-2: No ADR for timeout/streaming strategy

When timeout refactoring is implemented (v1.0 blocker), it should have an ADR documenting the per-operation timeout design.

**Action:** Create when implementing — `docs/adr/0005-timeout-strategy.md`

### M-3: No docs/archive/ directory yet

Decision Q4 confirmed: archive, never delete. The target directory doesn't exist.

**Action:** Create `docs/archive/` and document the policy in CONTRIBUTING.md

### M-4: No diagram index

`assets/diagrams/` has source files, `assets/exports/` has PNGs. No index or README explaining what each diagram shows.

**Action:** Add `assets/diagrams/README.md` or an index in docs

---

## docs/ folder structure — proposed

```
docs/
  adr/                          ← Architecture Decision Records (numbered)
  archive/                      ← Historical docs (moved at release, never deleted)
  audits/
    agent-files/                ← This audit set (active)
  ansible-roadmap.md            ← Phase 2 plan
  api-reference.md              ← Method signatures (kept per-repo, decision Q3)
  api-versions.md               ← Tested API versions
  credentials.md                ← Credential providers
  feature-coverage.md           ← Feature matrix
  hardening.md                  ← Security hardening
  licenses.md                   ← Dependency licenses
  refactor-clarification-2026-03-30.md  ← Decisions + priority matrix
```

**Removed/archived after verification:**
- `lib-summary.md` → archive (if redundant with README)
- `release-process.md` → archive (if covered by CONTRIBUTING.md)
- `devcontainer-platform-tests.md` → archive (if stale)
- `references.md` → keep if links are live, archive if not

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Update api-reference.md with all 10 managers | HIGH | Medium |
| A2 | Verify feature-coverage.md reflects current state | MEDIUM | Low |
| A3 | Verify api-versions.md includes newer API endpoints | MEDIUM | Low |
| A4 | Check lib-summary.md for redundancy with README | MEDIUM | Low |
| A5 | Check release-process.md for redundancy with CONTRIBUTING.md | MEDIUM | Low |
| A6 | Verify devcontainer-platform-tests.md relevance | LOW | Low |
| A7 | Check references.md for dead links | LOW | Low |
| A8 | Create docs/archive/ directory | LOW | Low |
| A9 | Create ADR-0004 for per-repo RAID decision | MEDIUM | Low |
| A10 | Add assets/diagrams/ index | LOW | Low |

---

## Design principles applied

- **Separation of concerns:** Each doc file has one clear purpose. Overlapping files are candidates for archival.
- **Single source of truth:** API reference is per-repo (decision Q3). No global doc duplicates it.
- **Archive, never delete:** Decision Q4. Historical files move to docs/archive/, preserving audit trail.
- **ADR discipline:** Every architectural decision gets an ADR. Missing ADRs are tracked.

---

*To apply: verify redundancy candidates first (A4, A5, A6, A7), then archive confirmed redundant files, then update stale docs.*
