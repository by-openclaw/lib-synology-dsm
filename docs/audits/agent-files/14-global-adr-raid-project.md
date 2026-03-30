# Audit: Global ADR System, RAID, and GitHub Project Board Sync

> **Scope:** `doc-platform-core/docs/adr/` (8 global ADRs), `doc-platform-core/docs/raid.md`, GitHub Projects board, cross-repo sync
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — project board automation missing, RAID sync broken, ADR cross-references incomplete

---

## Architecture: Two ADR levels

The platform uses a two-tier ADR system:

| Level | Location | Scope | Count |
|---|---|---|---|
| **Global (platform-wide)** | `doc-platform-core/docs/adr/` | All repos, all layers | 8 ADRs (0001–0008) |
| **Repo-level** | `{repo}/docs/adr/` | Single repo only | 3 in lib-synology-dsm, 0 in others |

**ADR-0006 (Platform Charter)** is the governing document — it defines layers, standards, and the RAID/Project board atomic rule. All repos reference it.

---

## Global ADRs — inventory

| ADR | Title | Status | Stale? |
|---|---|---|---|
| 0001 | Platform Stack Decisions | Accepted | **Partially** — locked for PoC, but some tool choices may have evolved |
| 0002 | Repository Structure and Naming | Accepted | Current |
| 0003 | Issue Tracking Standard (RAID + GitHub Projects) | Accepted | **YES** — the standard isn't being followed (see below) |
| 0004 | Identity & SSO Architecture (Authentik + EntraID) | Accepted | Current (Phase 2+) |
| 0005 | VCS & CI/CD Strategy (GitHub → GitLab) | Accepted | Current |
| 0006 | Platform Charter | Accepted | **Partially** — Layer status stale (says Layer 1 at 80%, Layer 4 is now active) |
| 0007 | Automation & Scripting Standard | Accepted | Current |
| 0008 | Terraform State Management | Accepted | Current |

---

## Cross-repo ADR adoption

| Repo | Has docs/adr/? | Own ADRs? | References ADR-0006? | RAID.md? |
|---|---|---|---|---|
| lib-synology-dsm | Yes | 3 (0001-0003) | Yes (CLAUDE.md) | No |
| doc-platform-core | Yes | 8 (0001-0008) | Yes (canonical source) | Yes (docs/raid.md) |
| ansible-platform | Yes (empty, README only) | 0 | Yes (CLAUDE.md, AGENTS.md, README) | No |
| infra-terraform-proxmox | Yes (empty, README only) | 0 | No | No |
| platform-setup | Yes (empty, README only) | 0 | Yes (CLAUDE.md, issue templates) | No |

---

## Problem #1: The RAID atomic rule is not enforced

**ADR-0003 and ADR-0006 §RAID state:**

> Every issue/risk/dependency triggers THREE simultaneous actions:
> 1. Entry in `doc-platform-core/docs/raid.md`
> 2. GitHub Issue on `by-openclaw/platform-setup` with RAID labels
> 3. GitHub Projects board (#1) entry

**Current reality:**

| Step | Implemented? | Evidence |
|---|---|---|
| RAID.md entries | **Partially** — 88+ items tracked, but not all recent decisions/issues are there | Last updated 2026-03-29, before the 2026-03-30 refactor decisions |
| GitHub Issues with RAID labels | **Partially** — issue templates exist (`raid-action.md`, `raid-risk.md`, `raid-dependency.md`) but usage is manual | No automation — agents and humans must remember to create issues |
| GitHub Projects board sync | **Not implemented** — zero `add-to-project` workflows exist across all 5 repos | ADR-0006 says it must happen. It doesn't. |

**This is the biggest gap in the entire platform governance system.** The atomic rule is the backbone of ADR-0003 and ADR-0006, and it's only partially followed.

---

## Problem #2: No project board automation

ADR-0006 §5.2.c from the refactor doc identified this:

> GitHub Projects board (by-openclaw/projects/1) must be auto-populated.

**Current state across all 5 repos:**

| Repo | Workflows | Any project board automation? |
|---|---|---|
| lib-synology-dsm | ci.yml, release-please.yml | No |
| doc-platform-core | release-please.yml | No |
| ansible-platform | release-please.yml, discord-notify.yml | No |
| infra-terraform-proxmox | terraform-ci.yml, release-please.yml, discord-notify.yml | No |
| platform-setup | release-please.yml, discord-notify.yml | No |

**Zero repos have `add-to-project` automation.** Every issue must be manually dragged to the board.

**Fix:** Add a shared workflow (or per-repo workflow) using `actions/add-to-project@v1`:

```yaml
# .github/workflows/project-board-sync.yml
name: Add to Project Board
on:
  issues:
    types: [opened]
  pull_requests:
    types: [opened]
jobs:
  add:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1.0.2
        with:
          project-url: https://github.com/orgs/by-openclaw/projects/1
          github-token: ${{ secrets.PROJECT_TOKEN }}
```

This needs an org-level PAT with `project` scope, stored as a shared secret.

---

## Problem #3: RAID.md is centralized but decision was per-repo

The 2026-03-30 refactor decisions confirmed: **per-repo RAID, not centralized.**

But currently:
- RAID.md exists only in `doc-platform-core/docs/raid.md` (centralized)
- No repo has its own RAID.md
- ADR-0003 says RAID entries go to `doc-platform-core/docs/raid.md`

**Conflict:** The lib-synology-dsm refactor decision (per-repo) contradicts ADR-0003 (centralized).

**Resolution needed:**

| Option | Pros | Cons |
|---|---|---|
| A: Per-repo RAID (lib-synology-dsm decision) | Separation of concerns, access-scoped | Fragmented view, harder to audit across platform |
| B: Centralized RAID (ADR-0003) | Single view, compliance-friendly | Access gaps, mixes repo concerns |
| C: Hybrid — per-repo for repo-scoped items, centralized for platform-wide | Best of both | More files to maintain |

**If per-repo wins:** ADR-0003 needs amendment or superseding. The current wording explicitly says `doc-platform-core/docs/raid.md`. Changing this is an architectural decision that needs a new ADR (or an amendment).

---

## Problem #4: ADR-0006 layer status is stale

ADR-0006 says:
> **Current status (2026-03-28):** Layer 0 in progress, Layer 1 at 80%.

As of 2026-03-30:
- Layer 4 (Storage / lib-synology-dsm) is active — v0.9.3 with 283 tests
- Layer 1 (Proxmox Base) has progressed — VMs deployed, Terraform operational
- Layer 0 (Standards) has progressed — ADRs, RAID, charter all established

**The charter doesn't reflect current progress.** This matters because ADR-0006 Rule #1 says "nothing proceeds to next layer until current layer is documented, tested, signed off." If the status in the charter shows Layer 1 at 80%, it looks like Layer 4 work violates the rule.

**Fix:** Update ADR-0006 status section. Or add a companion doc (`docs/layer-status.md`) that tracks current state separately from the decision record.

---

## Problem #5: No global ADR index with cross-references

`doc-platform-core/docs/adr/` has no README.md or index file. The 8 ADRs are listed as files but there's no:
- Table of all ADRs with status
- Cross-reference showing which repos depend on which ADR
- Relationship map (e.g., ADR-0006 references ADR-0003, ADR-0007)

**lib-synology-dsm has an index** (`docs/adr/README.md`) — the global level doesn't.

---

## Problem #6: Repo-level ADRs vs global ADRs — no convention

lib-synology-dsm has 3 repo-level ADRs. Other repos have 0. There's no convention for:
- When does a decision go in the repo ADR vs the global ADR?
- Can a repo-level ADR contradict a global ADR?
- How are repo ADR numbers managed? (lib-synology-dsm uses 0001–0003, same numbers as global)

**Number collision:** Global ADR-0001 = "Platform Stack Decisions." lib-synology-dsm ADR-0001 = "Use stdlib urllib." Different decisions, same number. An agent referencing "ADR-0001" is ambiguous.

**Fix — namespacing convention:**
- Global: `ADR-NNNN` (no prefix)
- Repo-level: `{REPO}-ADR-NNNN` (e.g., `LIB-ADR-0001`)
- Or: global uses `PADR-NNNN` (platform), repo uses `ADR-NNNN`

---

## Problem #7: discord-notify.yml still exists in some repos

The MEMORY.md (2026-03-29) says:
> Removed all discord-notify.yml workflows + DISCORD_WEBHOOK secrets from all repos + org level

But the exploration found `discord-notify.yml` still in:
- infra-terraform-proxmox
- ansible-platform
- platform-setup

Either MEMORY.md is wrong (removal didn't complete), or the files were re-added. **Verify and clean up.**

---

## Action items

| # | Action | Priority | Effort | Scope |
|---|---|---|---|---|
| A1 | Add `add-to-project` workflow to all 5 repos (or a shared org workflow) | HIGH | Medium | All repos |
| A2 | Resolve RAID location conflict: per-repo (refactor decision) vs centralized (ADR-0003) — write ADR amendment | HIGH | Low | Platform |
| A3 | Update ADR-0006 layer status to reflect current progress | HIGH | Low | doc-platform-core |
| A4 | Create global ADR index (README.md in doc-platform-core/docs/adr/) | MEDIUM | Low | doc-platform-core |
| A5 | Establish ADR namespacing convention (global vs repo-level, number collision) | MEDIUM | Low | Platform |
| A6 | Update RAID.md with 2026-03-30 refactor decisions | MEDIUM | Low | doc-platform-core (or per-repo) |
| A7 | Verify discord-notify.yml removal across all repos | MEDIUM | Low | All repos |
| A8 | Create ADR layer-status companion doc (separate volatile state from immutable decision) | LOW | Low | doc-platform-core |
| A9 | Add cross-reference table to global ADR index (which repos depend on which ADR) | LOW | Medium | doc-platform-core |

---

## Design principles applied

- **Atomic operations:** RAID + Issue + Board = one operation. If any step is manual, the atomicity is broken. Automate or accept the debt.
- **Decision traceability:** A repo-level decision that contradicts a global ADR is a governance gap, not a feature. Resolve with an amendment, not silence.
- **Separation of concerns:** Global ADRs = platform architecture. Repo ADRs = repo-specific implementation. Different scopes, different files, different numbering.
- **Immutable decisions, mutable state:** ADR-0006 is a decision (immutable). Layer progress is state (mutable). They shouldn't live in the same section.

---

*To apply: A1 (project board automation) and A2 (RAID location resolution) are the highest impact. A1 requires an org-level PAT. A2 requires a team decision — the current state is contradictory.*
