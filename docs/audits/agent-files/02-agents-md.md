# Audit: AGENTS.md

> **Scope:** `lib-synology-dsm/AGENTS.md`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — role overlap with CLAUDE.md, stale stats, unclear audience

---

## Purpose of AGENTS.md

AGENTS.md is the **universal agent onboarding file**. It is agent-agnostic — Claude, Codex, Gemini, Copilot, or a human contractor should all be able to read it and understand:

1. **What is this repo?** (one-liner)
2. **What do I read first?** (ordered reading list)
3. **What are the rules?** (coding standards, commit standards, health rules)
4. **What must I never do?** (guardrails)
5. **Who maintains this?** (ownership)

CLAUDE.md is the Claude-specific contract (hard rules, API quirks, DSM bugs). AGENTS.md should not duplicate it — it should reference it.

---

## Current state

- **Lines:** ~100
- **Last updated:** 2026-03-29 (Project Stats)
- **Sections:** 8 (Always Read First, Coding & Commit Standards, Health Rules, What NOT To Do, Known Blocker, GitHub Repo, Agent: Rune, Doc Maintenance, Project Stats)

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Always Read First (ordered reading list) | Strong | Clear priority order. Good pattern. |
| Coding & Commit Standards | Good | Conventional commits, PEP 8, branch naming. |
| Project Health Rules | Strong | Aligns with SOUL.md philosophy. Actionable. |
| Known Blocker (DSM account requirements) | Good | Practical, saves debugging time. |

---

## What's stale

| Item | Problem | Fix |
|---|---|---|
| Project Stats — Version | Says v0.9.0 | Verify current tagged version |
| Project Stats — Unit tests | Says 283 | Verify — CLAUDE.md also says 283, cross-check |
| Project Stats — Open issues | Says "3 HIGH (mypy, release path, verify_ssl)" | Release path decided. Update count and list. |
| Project Stats — mypy | Says "27 errors" | Verify current count |
| "No httpx" note | Says "httpx not available on Rune's host" | Misleading — the real reason is ADR-0001 (zero runtime deps). The host availability is irrelevant. |

---

## What's missing

### M-1: TrafficControlManager not mentioned

The opening description says "session management, user/group/share CRUD, NFS export rules, and FileStation file operations." Missing: quota, storage, bandwidth, traffic control.

**Fix:** Update description to reflect all 8 managers.

### M-2: No reference to refactor decisions

The confirmed decisions (per-repo docs, archive not delete, per-repo RAID, v1.0 blockers) are not referenced.

**Fix:** Add to "Always Read First" list:
```markdown
7. [`docs/refactor-clarification-2026-03-30.md`](docs/refactor-clarification-2026-03-30.md) — confirmed decisions and v1.0 priority matrix
```

### M-3: No v1.0 context

An agent reading AGENTS.md has no idea what the next milestone is or what's blocking it.

**Fix:** Add a "Current Milestone" section (3 lines max) pointing to the refactor doc.

---

## Structural issues

### S-1: Role overlap with CLAUDE.md (critical)

This is the biggest problem. AGENTS.md and CLAUDE.md duplicate each other significantly:

| Topic | AGENTS.md | CLAUDE.md | Who should own it? |
|---|---|---|---|
| "No httpx" | ✅ What NOT To Do | ✅ Hard Rules | **CLAUDE.md** (ADR-level) |
| Conventional Commits | ✅ Coding Standards | ✅ Commit discipline | **AGENTS.md** (universal standard) |
| ensure() pattern | ✅ "All new managers" | ✅ Hard Rules (ADR-0002) | **CLAUDE.md** (ADR-level) |
| DSM account blocker | ✅ Known Blocker | ✅ (not present) | **AGENTS.md** (operational) |
| API field gotchas | ✅ What NOT To Do | ✅ API Gotchas | **CLAUDE.md** (DSM-specific) |
| Definition of Done | ✅ (implied in Health Rules) | ✅ (checklist) | **SOUL.md** (canonical) |
| Project Stats | ✅ Stats table | ✅ Current State table | **One file only** |

**Current result:** An agent reads both files and sees the same information in slightly different words. When one gets updated and the other doesn't — they drift.

**Recommendation — clean separation:**

| File | Owns | Pattern |
|---|---|---|
| **AGENTS.md** | Onboarding, reading order, coding standards, commit format, health rules, operational blockers, ownership, project stats | **Strategy layer** — what and why |
| **CLAUDE.md** | Hard rules (ADRs), API quirks, DSM bugs, v1.0 blockers, current state (volatile), TLS decision | **Tactical layer** — how and what not to break |
| **SOUL.md** | Agent identity, DoD, professional standards, diagram standard | **Identity layer** — who I am (workspace-level) |

**Concrete actions to deduplicate:**
1. Remove "No httpx" from AGENTS.md What NOT To Do — it's in CLAUDE.md Hard Rules
2. Remove API field gotchas (`auth.cgi`, `X-SYNO-TOKEN`, `sharename`, `name_org`) from AGENTS.md — they're in CLAUDE.md API Gotchas
3. Remove "Do NOT check top-level `success`" from AGENTS.md — CLAUDE.md territory
4. Keep in AGENTS.md What NOT To Do: only items that are universal (not Claude-specific, not DSM-specific)
5. Remove Project Stats from one file — keep in AGENTS.md (it's the onboarding doc), remove Current State table from CLAUDE.md or make it a reference link

### S-2: "What NOT To Do" mixes concerns

Current list has 8 items mixing three different scopes:

| Item | Scope | Should live in |
|---|---|---|
| Do NOT use httpx | Architecture (ADR) | CLAUDE.md Hard Rules |
| Do NOT use auth.cgi | DSM API quirk | CLAUDE.md API Gotchas |
| Do NOT skip X-SYNO-TOKEN | DSM API quirk | CLAUDE.md API Gotchas |
| Do NOT check top-level success | DSM API quirk | CLAUDE.md API Gotchas |
| Do NOT use sharename param | DSM API quirk | CLAUDE.md API Gotchas |
| Do NOT omit name_org | DSM API quirk | CLAUDE.md API Gotchas |
| Do NOT run integration tests without checking blocker | Operational | AGENTS.md (keep) |
| Do NOT publish to PyPI without instruction | Operational | AGENTS.md (keep) |

**After cleanup, AGENTS.md "What NOT To Do" should have 2-3 items max**, all operational. DSM-specific items belong in CLAUDE.md.

### S-3: "My Lord" reference in AGENTS.md

Line 49: "Do NOT publish to PyPI without explicit instruction from My Lord"

AGENTS.md is agent-agnostic. Non-Claude agents won't know who "My Lord" is. Use "@yboujraf" or "the repo owner" in AGENTS.md. "My Lord" is appropriate in SOUL.md, USER.md, MEMORY.md (Rune's personal files).

### S-4: Doc Maintenance section is a process, not a reference

The "After Every Successful Build" section describes a workflow. This belongs in CONTRIBUTING.md or a CI checklist, not in an onboarding doc. An agent reading AGENTS.md for the first time doesn't need to know the post-build ritual — it needs to know the rules.

**Move to:** CONTRIBUTING.md as a "Post-Release Checklist" section.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Deduplicate: remove DSM API gotchas from What NOT To Do (keep in CLAUDE.md) | HIGH | Low |
| A2 | Deduplicate: remove "No httpx" from AGENTS.md (keep in CLAUDE.md Hard Rules) | HIGH | Low |
| A3 | Update opening description to include all 8 managers | HIGH | Low |
| A4 | Update Project Stats (version, test count, open issues, mypy) | HIGH | Low |
| A5 | Add refactor decisions doc to "Always Read First" list | MEDIUM | Low |
| A6 | Add "Current Milestone" section (3 lines, references refactor doc) | MEDIUM | Low |
| A7 | Replace "My Lord" with "@yboujraf" in AGENTS.md | MEDIUM | Low |
| A8 | Move Doc Maintenance section to CONTRIBUTING.md | LOW | Low |
| A9 | Fix "No httpx" rationale — ADR-0001, not host availability | LOW | Low |
| A10 | Decide: Project Stats in AGENTS.md only, or CLAUDE.md only — not both | MEDIUM | Low |

---

## Design principles applied

- **Separation of concerns:** AGENTS.md = universal onboarding. CLAUDE.md = Claude-specific contract. SOUL.md = agent identity. No topic lives in two files.
- **Single responsibility:** Each "What NOT To Do" item has exactly one owner file. DSM quirks → CLAUDE.md. Operational guardrails → AGENTS.md.
- **Interface segregation:** An agent that only reads AGENTS.md gets enough to start safely. An agent that also reads CLAUDE.md gets DSM-specific depth. Neither file requires the other to be complete.
- **DRY:** Project Stats appears once. DoD appears once (SOUL.md). Duplicated content is the primary source of drift.

---

*To apply: read this audit, confirm actions, then run agent with instructions to execute A1–A10.*
