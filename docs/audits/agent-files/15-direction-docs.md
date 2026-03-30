# Audit: Platform Direction Documents (roadmap, stack, architecture, RAID, charter)

> **Scope:** `doc-platform-core/docs/` — the "north star" files that define where the platform is going
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — stale status, gap report superseded, no single "where are we now" view

---

## Purpose

These files collectively answer:

1. **Where are we going?** → `roadmap.md` (phases, milestones, exit criteria)
2. **What are we building with?** → `stack.md` (locked tool choices)
3. **How is it structured?** → `architecture.md` (diagrams, layers, flows)
4. **What could go wrong?** → `raid.md` (risks, issues, dependencies)
5. **What are the rules?** → `adr/0006-platform-charter.md` (layers, standards, atomic rules)
6. **What's the current state?** → **nowhere** (this is the gap)

---

## Inventory

| File | Last updated | Status |
|---|---|---|
| `docs/roadmap.md` | 2026-03-25 | Phase model solid. **5 days stale** — no progress updates since. |
| `docs/stack.md` | 2026-03-25 | Locked for PoC. Current. |
| `docs/architecture.md` | 2026-03-25 | Draft — PlantUML diagrams. **5 days stale.** |
| `docs/raid.md` | 2026-03-29 | Active — 88+ items. **1 day stale** (missing 2026-03-30 refactor decisions). |
| `docs/adr/0006-platform-charter.md` | 2026-03-28 | Accepted. **Layer status stale** (says L1 at 80%). |
| `docs/idempotency-strategy.md` | 2026-03-26 | Active. Current. |
| `docs/naming-convention.md` | ~2026-03-25 | Active. Current. |
| `docs/lib-synology-dsm-gap-report-2026-03-29.md` | 2026-03-29 | **Superseded** — most gaps have been fixed. |
| `docs/vm-template-spec.md` | unknown | Not reviewed. |
| `docs/netbox.md` | unknown | Not reviewed. |
| `docs/concepts/odoo-platform-orchestration.md` | unknown | Concept doc. |
| `docs/templates/` | unknown | 4 templates (CLAUDE, CONTRIBUTING, README, SOW). |
| `docs/archive/brainstorm-2026-03-25.md` | 2026-03-25 | Archived — initial brainstorm. |

---

## What's good

| File | Verdict | Notes |
|---|---|---|
| `roadmap.md` | Strong | Clean phase model with dependencies and exit criteria. Tier 1/2 split is clear. |
| `stack.md` | Strong | Comprehensive inventory, locked for PoC, no ambiguity. |
| `architecture.md` | Good | 5 PlantUML diagrams covering all major views. |
| `raid.md` | Strong | 88+ items, severity tagged, owner assigned, review cadence defined. |
| `idempotency-strategy.md` | Good | Clear principles, per-tool patterns. |
| `docs/templates/` | Good | Standardized repo templates (CLAUDE, CONTRIBUTING, README, SOW). |

---

## Critical gap: No "current status" view

The platform has files for **where we're going** (roadmap), **what we're building with** (stack), **what could go wrong** (RAID), and **what the rules are** (charter). But there is **no file that answers: "where are we right now?"**

An agent (or team member) picking up the project today must cross-reference:
- ADR-0006 Layer status (stale: "L1 at 80%")
- RAID.md open items (88+ items, mixed with resolved)
- Each repo's CLAUDE.md current state table
- CHANGELOG.md across 5 repos

**There is no single view of current platform progress.**

### Proposed: `docs/status.md`

A live-updated file — volatile state separated from immutable decisions:

```markdown
# Platform Status

> Last updated: YYYY-MM-DD

## Layer Progress

| Layer | Name | Status | Completion | Blockers |
|---|---|---|---|---|
| 0 | Standards & Templates | In progress | ~90% | ADR-0003/0006 RAID conflict |
| 1 | Proxmox Base | In progress | ~85% | OPNsense VM, vmbrPOC bridge |
| 2 | Vault | Not started | 0% | Blocked on Layer 1 |
| 3 | Identity | Not started | 0% | Blocked on Layer 2 |
| 4 | Storage | Active | ~80% | lib-synology-dsm v1.0 blockers |
| 5 | PoC Services | Not started | 0% | Blocked on Layers 2–4 |

## Per-Repo Status

| Repo | Version | Tests | Key blocker |
|---|---|---|---|
| lib-synology-dsm | v0.9.3 | 283 unit, 51 integration | Timeout, upload return dict, mypy |
| infra-terraform-proxmox | — | — | OPNsense VM scaffold |
| ansible-platform | — | — | Hardening roles only |
| doc-platform-core | v0.5.0 | n/a (docs only) | — |
| platform-setup | — | — | — |

## Critical RAID items (top 5)

[Pulled from raid.md — just the top blockers]
```

**Update trigger:** After any release, layer change, or RAID update.
**Owner:** Whoever (agent or human) makes the change updates status.md.

---

## Stale files

### `docs/lib-synology-dsm-gap-report-2026-03-29.md` — superseded

This report identified 15 critical + 22 high gaps in lib-synology-dsm. Since then:
- Exception hierarchy: **done** (v0.7.3)
- ensure() idempotency: **done** (all 7+ managers)
- dry_run: **done** (all managers)
- Unit tests: **done** (283 tests, 100% coverage)
- CI: **done** (ruff + mypy + pytest + bandit)

**Most of the 15 critical gaps are resolved.** This report now gives a false impression of the library state.

**Action:** Move to `docs/archive/`. Replace with a reference to `lib-synology-dsm/docs/refactor-clarification-2026-03-30.md` for current gaps.

### `docs/architecture.md` — VLAN numbers may not match reality

Architecture diagrams show VLAN IDs (10, 20, 30, 40, 50, 60, 99). ADR-0006 and MEMORY.md show different IP ranges (10.6.224.0/24, 10.6.225.0/24, etc.). These may be different abstraction levels (logical VLANs vs PoC IPs), but it's not stated.

**Action:** Add a note clarifying whether architecture.md shows target-state or PoC-state.

### `roadmap.md` — no progress tracking

The roadmap defines phases and exit criteria but has **no status column**. You can't tell which exit criteria are met without checking each repo.

**Action:** Add a status/progress indicator to each phase, or reference `docs/status.md` (proposed above).

---

## ADR-0006 — layer rule compliance

ADR-0006 Rule #1: "Nothing proceeds to next layer until current layer is documented, tested, signed off."

**Current reality:**
- Layer 0 (Standards): ~90% — charter exists, naming exists, templates exist. Gap: RAID location conflict unresolved.
- Layer 1 (Proxmox Base): ~85% — VMs deploy, Terraform works. Gap: OPNsense VM, vmbrPOC bridge not done.
- Layer 4 (Storage): Active at v0.9.3 — but Layer 2 (Vault) and Layer 3 (Identity) haven't started.

**Is Layer 4 work a rule violation?** Technically yes — Layers 2 and 3 are unfinished. But lib-synology-dsm is a library (no infra dependency on Vault/Identity). It can be developed in parallel without violating the spirit of the rule.

**Recommendation:** Either:
- Amend ADR-0006 to note that libraries (Layer 4) can be developed in parallel with infrastructure layers
- Or document the exception explicitly in status.md

---

## RAID.md — update needed

Missing from RAID.md (confirmed 2026-03-30):
- Per-repo RAID decision (conflicts with ADR-0003)
- Per-language repos decision
- lib-synology-dsm v1.0 blockers (timeout, upload return dict, return dict audit)
- Archive-never-delete policy
- ADR number collision (global vs repo-level)
- Project board automation gap

These are all identified risks/issues/decisions that should be tracked.

---

## doc-platform-core templates — useful but not audited

`docs/templates/` contains 4 standardized templates:
- `CLAUDE.tpl.md` — template for per-repo CLAUDE.md
- `CONTRIBUTING.tpl.md` — template for per-repo CONTRIBUTING.md
- `README.tpl.md` — template for per-repo README.md
- `sow.tpl.md` — Statement of Work template

**These are valuable** — they enforce consistency across repos. But the per-repo audits (01-claude-md, 06-contributing-md, 07-readme-md) show that actual files have drifted from templates. Templates should be updated to reflect audit recommendations.

**Action:** After applying audit recommendations to lib-synology-dsm files, backport the improved structure into `docs/templates/`.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Create `docs/status.md` — live platform status view | HIGH | Medium |
| A2 | Archive `lib-synology-dsm-gap-report-2026-03-29.md` — superseded | HIGH | Low |
| A3 | Update ADR-0006 layer status or separate into status.md | HIGH | Low |
| A4 | Update RAID.md with 2026-03-30 decisions and new risks | HIGH | Medium |
| A5 | Add progress tracking to roadmap.md (status column or reference to status.md) | MEDIUM | Low |
| A6 | Clarify architecture.md — target-state vs PoC-state diagrams | MEDIUM | Low |
| A7 | Document Layer 4 parallel development exception (ADR amendment or status.md note) | MEDIUM | Low |
| A8 | Backport audit-improved file structures into docs/templates/ | LOW | Medium |
| A9 | Verify discord-notify.yml removal (flagged in audit 14, P-7) | LOW | Low |

---

## Design principles applied

- **Separation of mutable and immutable:** Decisions (ADRs) are immutable. Status is mutable. They don't belong in the same document. `docs/status.md` separates what was decided from where we are.
- **Single source of truth:** "Where are we now?" should have exactly one answer, in one file. Currently it requires cross-referencing 5+ files.
- **Archive superseded content:** The gap report is a snapshot. The snapshot is stale. Archive it and point to the current truth.
- **Fail-fast for newcomers:** An agent or team member joining today should read `status.md` → `roadmap.md` → `stack.md` in that order and know everything in 5 minutes.

---

*To apply: A1 (create status.md) is the highest-value action. It fills the "where are we now" gap that no existing file covers. A2 and A3 are quick cleanup.*
