# Audit: Full Project Documentation — Overview

> **Scope:** All agent context files, documentation, configuration, and templates for lib-synology-dsm
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Total audits:** 16 files across 6 categories

---

## Files audited

### Agent context files (workspace + repo level)

| # | File | Location | Scope | Verdict | Audit |
|---|---|---|---|---|---|
| 01 | CLAUDE.md | `lib-synology-dsm/` | Repo | Stale + structural | [01-claude-md.md](01-claude-md.md) |
| 02 | AGENTS.md | `lib-synology-dsm/` | Repo | Duplication with CLAUDE.md | [02-agents-md.md](02-agents-md.md) |
| 03 | SOUL.md | `workspace/` | Workspace | Scope creep — has operational content | [03-soul-md.md](03-soul-md.md) |
| 04 | MEMORY.md | `workspace/` | Workspace | Unbounded growth, mixed concerns | [04-memory-md.md](04-memory-md.md) |
| 05 | USER.md | `workspace/` | Workspace | Cleanest file — minor tweaks | [05-user-md.md](05-user-md.md) |

### Developer & contribution files

| # | File | Location | Scope | Verdict | Audit |
|---|---|---|---|---|---|
| 06 | CONTRIBUTING.md | `lib-synology-dsm/` | Repo | Missing sections — will receive content from SOUL.md/AGENTS.md | [06-contributing-md.md](06-contributing-md.md) |
| 07 | README.md | `lib-synology-dsm/` | Repo | Good — minor staleness risk | [07-readme-md.md](07-readme-md.md) |
| 08 | CHANGELOG.md | `lib-synology-dsm/` | Repo | Healthy — auto-managed | [08-changelog-md.md](08-changelog-md.md) |

### Security & compliance

| # | File | Location | Scope | Verdict | Audit |
|---|---|---|---|---|---|
| 09 | SECURITY.md + hardening.md | `lib-synology-dsm/` | Repo | Stale version, scope overlap | [09-security-md.md](09-security-md.md) |

### Infrastructure & config

| # | File | Location | Scope | Verdict | Audit |
|---|---|---|---|---|---|
| 10 | GitHub templates + CODEOWNERS | `.github/` | Repo | Functional — label enforcement missing | [10-github-templates.md](10-github-templates.md) |
| 11 | docs/ folder | `docs/` | Repo | Redundancy + staleness + missing ADRs | [11-docs-folder.md](11-docs-folder.md) |
| 12 | pyproject.toml | `lib-synology-dsm/` | Repo | Healthy — minor gaps | [12-pyproject-toml.md](12-pyproject-toml.md) |
| 13 | ADRs (docs/adr/) | `docs/adr/` | Repo | 3 existing OK, 5 decisions missing ADRs | [13-adr.md](13-adr.md) |
| 14 | Global ADRs + RAID + Project Board | `doc-platform-core/` + all repos | Platform | RAID atomic rule not enforced, board automation missing, RAID location conflict | [14-global-adr-raid-project.md](14-global-adr-raid-project.md) |
| 15 | Direction docs (roadmap, stack, architecture, RAID, charter) | `doc-platform-core/docs/` | Platform | No "current status" view, gap report superseded, layer rule compliance question | [15-direction-docs.md](15-direction-docs.md) |
| 16 | Secrets redaction | All workspace + repos | Security | Discord webhook token EXPOSED, password in 6+ files, SSH keys in docs | [16-secrets-redaction.md](16-secrets-redaction.md) |

---

## Cross-cutting findings

### F-1: No ownership model — content lives in multiple files

The biggest systemic issue. The same content appears in 2-3 files with slightly different wording. When one is updated, the others drift.

**Proposed ownership model:**

| Content | Single owner | Others |
|---|---|---|
| Agent identity (who Rune is) | SOUL.md | — |
| Human identity (who My Lord is) | USER.md | MEMORY.md references only |
| Definition of Done | SOUL.md (principles) + CONTRIBUTING.md (checklist) | CLAUDE.md, AGENTS.md reference only |
| Commit & version standard | AGENTS.md or CONTRIBUTING.md | SOUL.md references only |
| Diagram standard | CONTRIBUTING.md | SOUL.md references only |
| Hard rules (urllib, ensure, creds) | CLAUDE.md | AGENTS.md references only |
| API quirks (DSM-specific) | CLAUDE.md | — |
| Current state (volatile) | CLAUDE.md | — |
| Project stats | AGENTS.md | — |
| Standing rules (policy) | MEMORY.md | — |
| Historical decisions | MEMORY-archive.md (new) | — |
| Coding standards (universal) | AGENTS.md | — |
| Operational blockers | AGENTS.md | — |

**Rule: if a topic has two owners, one of them is wrong.**

### F-2: No file hierarchy documented anywhere

Five files, two scopes (workspace / repo), no map. An agent discovering these files doesn't know the reading order or precedence.

**Proposed hierarchy:**

```
Workspace level (read once, applies everywhere):
  SOUL.md      → who the agent is
  USER.md      → who the human is
  MEMORY.md    → what the agent remembers

Repo level (read per-repo, specific context):
  AGENTS.md    → onboarding for any agent (universal)
  CLAUDE.md    → Claude-specific contract (tactical)
```

**Reading order for a new agent:**
1. SOUL.md (identity)
2. USER.md (human context)
3. AGENTS.md (repo onboarding)
4. CLAUDE.md (repo-specific rules)
5. MEMORY.md (session context — on demand, not upfront)

### F-3: No lifecycle management across files

| File | Has update policy? | Has archive mechanism? | Has size cap? |
|---|---|---|---|
| CLAUDE.md | No | No | No |
| AGENTS.md | Yes (after every build) | No | No |
| SOUL.md | Partial ("mine to evolve") | No | No |
| MEMORY.md | No | No | No |
| USER.md | No | No | No |

**Recommendation:** Each file gets a 2-line update policy at the bottom:
- **When** to update (trigger)
- **What** to archive vs keep (lifecycle)

---

## Total action items: 68 across 12 audits

### Tier 1 — Must-do (team alignment required)

| # | Action | Source audit | Why |
|---|---|---|---|
| 1 | Define single ownership model for each content type | 00-overview | Stops drift permanently — the root cause of most issues |
| 2 | Move Hard Rules to top of CLAUDE.md | 01 | Fail-fast for agents |
| 3 | Add v1.0 Blockers section to CLAUDE.md | 01 | No agent knows the goal |
| 4 | Deduplicate AGENTS.md vs CLAUDE.md (8 overlapping items) | 02 | Same content, different words, guaranteed drift |
| 5 | Create MEMORY-archive.md + set 80-line cap on MEMORY.md | 04 | File will grow unbounded — 282 lines and rising |
| 6 | Move operational content out of SOUL.md (commit standard, diagram pipeline, DoD checklist) | 03 | Identity file contains process details |
| 7 | CONTRIBUTING.md receives moved content (commit standard, DoD checklist, diagram pipeline, post-release checklist) | 06 | Destination for content factored out of SOUL.md and AGENTS.md |
| 8 | Update CLAUDE.md current state (TrafficControlManager, bandwidth ensure, test count) | 01 | Stale — missing entire module |
| 9 | Update api-reference.md with all 10 managers | 11 | Decision Q3: keep per-repo, but must be current |
| 10 | Remove security-sensitive content from MEMORY.md (SSH keys, credential hints) | 04 | Plain text file read by every agent session |
| 11b | Fix ADR-0001 (pydantic reference) + ADR-0002 (stale manager list, return dict scope) | 13 | Existing ADRs have inaccuracies |
| 11c | Create ADR-0004 (per-repo RAID) + ADR-0005 (per-language repos) + ADR-0007 (return dict contract) | 13 | 5 confirmed decisions have no ADR — rules without anchors |
| 12a | Add `add-to-project` workflow to all 5 repos | 14 | RAID atomic rule (ADR-0003/0006) says Issue+Board+RAID.md. Board step = zero automation. |
| 12b | Resolve RAID location conflict: per-repo (refactor Q3) vs centralized (ADR-0003) | 14 | Two decisions contradict each other — one must be amended |
| 12c | Update ADR-0006 layer status (says Layer 1 at 80% — Layer 4 is active) | 14 | Charter doesn't reflect current progress, looks like rule violation |
| 13a | Create `doc-platform-core/docs/status.md` — live platform status view | 15 | No single file answers "where are we now?" — requires cross-referencing 5+ files |
| 13b | Archive `lib-synology-dsm-gap-report-2026-03-29.md` — superseded by actual progress | 15 | Gap report says 15 critical gaps; most are now fixed. Gives false impression. |
| 13c | Update RAID.md with 2026-03-30 decisions and new identified risks | 15 | RAID is 1 day stale — missing refactor decisions, v1.0 blockers, RAID location conflict |

### Tier 2 — Should-do (quality improvement)

| # | Action | Source audit | Why |
|---|---|---|---|
| 11 | Add file hierarchy / reading order to SOUL.md | 03 | Agents need a map |
| 12 | Reorganize MEMORY.md by topic (not date) | 04 | Chronological doesn't scale |
| 13 | Update SECURITY.md supported version (0.8.x → 0.9.x) | 09 | Stale, visible to external reporters |
| 14 | Add `Closes #___` and label enforcement to GitHub templates | 10 | Refactor doc §5.2 — issue automation gaps |
| 15 | Verify + update feature-coverage.md, api-versions.md | 11 | May not reflect newer managers |
| 16 | Check docs for redundancy (lib-summary.md, release-process.md) | 11 | Archive if redundant |
| 17 | Create ADR-0004 for per-repo RAID decision | 11 | Architectural decision without ADR |
| 18 | Add v1.0 roadmap one-liner to README | 07 | Sets expectations for readers |
| 19 | Verify coverage threshold alignment (80% gate vs 100% claim) | 10, 12 | PR template, pyproject, and README disagree |

### Tier 3 — Nice-to-have

| # | Action | Source audit | Why |
|---|---|---|---|
| 20 | Add update policies to all files | 03, 04, 05 | Lifecycle clarity |
| 21 | Replace "My Lord" with @yboujraf in AGENTS.md | 02 | Agent-agnostic audience |
| 22 | Add "How to disagree" guidance in USER.md | 05 | Communication refinement |
| 23 | Add nox to dev deps + document in CONTRIBUTING.md | 06, 12 | Multi-python testing locally |
| 24 | Create docs/archive/ directory | 11 | Target for Q4 decision (archive, never delete) |
| 25 | Add assets/diagrams/ index | 11 | No README explaining what each diagram shows |

---

## How to apply these audits

1. **Review as a team** — read each audit, discuss, confirm or reject actions
2. **Create issues** — one GitHub issue per audit file, link to the audit
3. **Apply per-file** — each audit is self-contained, can be executed independently
4. **Verify** — after applying, re-read the file and confirm no duplication was introduced
5. **Archive these audits** — move to `docs/archive/` after all actions complete

---

## Dependency graph — what must happen in what order

Some actions are independent. Others must be coordinated.

```
Tier 1 critical path:

  [1] Define ownership model
       │
       ├──→ [6] Move content OUT of SOUL.md ──→ [7] Move content INTO CONTRIBUTING.md
       │
       ├──→ [4] Deduplicate AGENTS.md vs CLAUDE.md
       │         ├──→ [2] Reorder CLAUDE.md (hard rules first)
       │         └──→ [3] Add v1.0 blockers to CLAUDE.md
       │
       ├──→ [5] Create MEMORY-archive.md
       │         └──→ [10] Remove secrets from MEMORY.md
       │                └──→ [12] Reorganize MEMORY.md by topic
       │
       └──→ [8] Update CLAUDE.md current state
                └──→ [9] Update api-reference.md

Independent (can run in parallel with anything):
  [11] File hierarchy in SOUL.md
  [13] SECURITY.md version update
  [14] GitHub template fixes
  [15-16] docs/ verification + cleanup
  [17] ADR-0004
  [18] README v1.0 one-liner
```

**Recommended execution order:**
1. Agree on ownership model (team discussion — 15 min)
2. Execute moves: SOUL.md → CONTRIBUTING.md (atomic — one PR)
3. Execute deduplication: AGENTS.md ↔ CLAUDE.md (one PR)
4. Execute MEMORY.md restructure (one PR — workspace level)
5. Everything else in parallel (individual PRs or one batch)

---

*These audits are idempotent: applying the same recommendations twice produces the same result. They are independent at the audit level (each file can be analyzed alone) but coordinated at the execution level (content moves must be atomic). They follow separation of concerns: each audit owns exactly one file.*
