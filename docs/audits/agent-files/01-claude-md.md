# Audit: CLAUDE.md

> **Scope:** `lib-synology-dsm/CLAUDE.md`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — stale content, missing sections, structural issues

---

## Purpose of CLAUDE.md

CLAUDE.md is the **repo-level agent contract**. Any Claude agent (or subagent) picking up this repo reads CLAUDE.md first. It must answer three questions in order:

1. **What must I never do?** (hard rules)
2. **What is the current state?** (what exists, what's broken)
3. **What is the goal?** (what v1.0 looks like, what's blocking it)

Currently, the file answers #1 well, #2 partially, and #3 not at all.

---

## Current state

- **Lines:** ~150
- **Last updated header:** v0.9.0 — 2026-03-29
- **Sections:** 10 (Key Files, Current State, Open Issues, DSM Bugs, API Gotchas, Hard Rules, Constraints, Diagram Standard, Related)

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Hard rules (urllib, ensure, credentials, TLS, commits) | Strong | Non-negotiable, clear, referenced to ADRs. Keep as-is. |
| API gotchas | Strong | Saves real debugging time. Field-tested. |
| DSM version bugs | Good | Specific, version-pinned, workaround stated. |
| Definition of Done checklist | Good | Aligns with SOUL.md. |

---

## What's stale

| Item | Problem | Fix |
|---|---|---|
| Current State table — missing TrafficControlManager | New module shipped, not listed | Add row: `TrafficControlManager (CRUD + ensure_rule)` |
| Current State table — "Bandwidth manager" | Has `ensure_user()`/`ensure_group()` now, label is vague | Update to: `Bandwidth manager (read + write + ensure)` |
| Current State table — test count | Says 223, actual is 283 | Update to 283 |
| Open Issues — "Two release paths" | Decision made: Release Please canonical, release.sh removed | Remove or mark resolved |
| Open Issues — "API reference lags code" | Decision made (Q3): keep per-repo, separate of concerns | Update status |
| Related — GitHub Issues link | Points to `platform-setup/issues` | Should point to `lib-synology-dsm/issues` |

---

## What's missing

### M-1: v1.0 definition (critical)

No agent reading this file knows what "stable" means. The refactor doc defines v1.0 blockers but CLAUDE.md doesn't reference them.

**Add section: "v1.0 Blockers"**
```markdown
## v1.0 Blockers
- [ ] Timeout: per-operation defaults + streaming upload (client.py:69 hardcoded at 30s)
- [ ] FileStation.upload() return dict: `{"skipped": bool}` → `{"changed": bool, "action": str}`
- [ ] Return dict audit: all managers consistent `{"changed": bool, "action": str}`
- [ ] QuotaManager.ensure() — done
- [ ] BandwidthManager.ensure_user()/ensure_group() — done
- [ ] StorageManager.ensure() read-assert — done

See: docs/refactor-clarification-2026-03-30.md §5 Priority Matrix
```

### M-2: TrafficControlManager

Not mentioned anywhere in CLAUDE.md. Needs entry in:
- Current State table
- Key Files (if it has its own module file)

### M-3: Reference to refactor decisions

The confirmed decisions (per-repo docs, archive not delete, separate repos per language, RAID per-repo) are not referenced. Add to Related section:
```markdown
- Refactor decisions: `docs/refactor-clarification-2026-03-30.md` §6 Decisions Log
```

### M-4: Per-repo RAID reference

Decision was per-repo RAID (not centralized). CLAUDE.md still says:
> RAID: `doc-platform-core/docs/raid.md`

Update to local RAID.md once created. Until then, flag as pending.

### M-5: FileStation upload inconsistency

Known violation of the ensure pattern hard rule. Should be in Open Issues:
```markdown
| HIGH | FileStation.upload() returns {"skipped": bool} — violates ensure return dict | v1.0 blocker |
```

### M-6: Timeout gap

Hardcoded `timeout=30` in `client.py:69`. No per-operation, no retry, no streaming. Should be in Open Issues as v1.0 blocker.

---

## Structural issues

### S-1: Hard rules are buried at line ~80

An agent reads top to bottom. The hard rules are the most important section but they sit below Current State, Open Issues, DSM Bugs, and API Gotchas.

**Recommendation:** Move Hard Rules to immediately after "What This Repo Does." Order should be:
1. What This Repo Does
2. Hard Rules
3. v1.0 Blockers (new)
4. Current State
5. Open Issues
6. Key Files
7. API Gotchas
8. DSM Version Bugs
9. Constraints
10. Related

**Rationale:** An agent that violates a hard rule in the first 10 seconds of work causes more damage than one that doesn't know the test count. Front-load the guardrails.

### S-2: No layering signal

The file reads as a flat list. No indication of what's "read once and internalize" vs "check every time." Consider grouping:

- **Immutable** (hard rules, constraints) — read once
- **Volatile** (current state, open issues, v1.0 blockers) — check every session
- **Reference** (API gotchas, DSM bugs, diagrams) — consult when relevant

### S-3: Duplication with SOUL.md

Definition of Done appears in both CLAUDE.md and SOUL.md. CLAUDE.md should reference SOUL.md for the canonical DoD, not duplicate it. Duplication creates drift.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Move Hard Rules to position 2 (after What This Repo Does) | HIGH | Low |
| A2 | Add v1.0 Blockers section | HIGH | Low |
| A3 | Update Current State table (TrafficControlManager, bandwidth ensure, test count) | HIGH | Low |
| A4 | Update Open Issues (remove resolved, add timeout + upload dict) | HIGH | Low |
| A5 | Add reference to refactor decisions doc | MEDIUM | Low |
| A6 | Update RAID pointer to per-repo | MEDIUM | Low |
| A7 | Fix GitHub Issues link (platform-setup → lib-synology-dsm) | MEDIUM | Low |
| A8 | Reference SOUL.md for DoD instead of duplicating | LOW | Low |
| A9 | Add layering signal (immutable / volatile / reference grouping) | LOW | Medium |

---

## Design principles applied

- **Separation of concerns:** CLAUDE.md = repo contract. SOUL.md = agent identity. No overlap.
- **Idempotent:** Applying these changes twice produces the same result. No additive drift.
- **Single source of truth:** DoD lives in SOUL.md. v1.0 definition lives in refactor doc. CLAUDE.md references, not duplicates.
- **Fail-fast:** Hard rules first. An agent that reads 10 lines and stops should still know the guardrails.

---

*To apply: read this audit, confirm actions, then run agent with instructions to execute A1–A9.*
