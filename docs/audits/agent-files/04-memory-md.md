# Audit: MEMORY.md

> **Scope:** `/home/by-systems/.openclaw/workspace/MEMORY.md` (workspace-level)
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — unbounded growth, mixed concerns, no lifecycle management

---

## Purpose of MEMORY.md

MEMORY.md is the agent's **persistent long-term memory** across sessions. It answers:

1. **What happened?** (decisions, events, outcomes)
2. **What's the current truth?** (standing rules, standards, key facts)
3. **What do I need to know about the human?** (preferences, context)

It is the primary mechanism for session continuity. When Rune wakes up, MEMORY.md is what makes the new session feel like a continuation.

---

## Current state

- **Location:** `/home/by-systems/.openclaw/workspace/MEMORY.md`
- **Lines:** ~282
- **Last updated:** 2026-03-29
- **Sections:** ~15 (Human, Commitments, Standing Rules, Decisions by date, Session notes, GitHub webhook standard, OpenClaw upgrade)

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Human section | Good | Clear, concise identity of the owner. |
| Standing Rules | Good | Actionable, enforceable. Test fails → issue first. |
| Decisions — structured by date | Reasonable | Chronological decisions with context. |
| Subagent Transparency Protocol | Good | Clear 3-step protocol. |

---

## What's problematic

### P-1: Unbounded append-only growth (critical)

MEMORY.md is 282 lines and growing. Every session appends decisions, session notes, and operational details. At this rate:
- 10 sessions → ~500 lines
- 50 sessions → ~2500 lines
- Context window cost increases linearly

**There is no archival, no pruning, no lifecycle.** Old decisions (e.g., "First VM created: vm-netbox-poc-01") persist forever at the same priority as current standing rules.

**Pattern: Event Sourcing without Snapshots.** Every event is recorded but never compacted. The agent must replay the entire history to derive current state.

**Recommendation — tiered memory architecture:**

```
MEMORY.md          ← HOT: Standing rules, current truths, human context (~50 lines max)
MEMORY-archive.md  ← COLD: Historical decisions, session notes (append-only, rarely read)
```

**Rules:**
- MEMORY.md has a hard cap: ~80 lines. If adding a new entry pushes past 80, archive the oldest decision block.
- Standing Rules and Human sections are permanent (never archived).
- Date-specific decisions move to archive after they're implemented and verified.
- Session notes move to archive at end of session.

### P-2: Mixed abstraction levels

MEMORY.md mixes:

| Content type | Example | Abstraction |
|---|---|---|
| Human identity | "Address as My Lord" | Permanent context |
| Standing rules | "Test fails → open issue first" | Policy (stable) |
| Architecture decisions | "VCS Strategy: GitHub Phase 1, GitLab Phase 2" | Decision (semi-stable) |
| Operational state | "vm-debian-bootstrap-test-01 (ID 100), IP 10.6.225.11" | Volatile fact |
| Session diary | "Spawned audit subagent → gap report" | Ephemeral event |
| Credentials/IPs | "10.6.224.6", SSH keys, passwords | Security-sensitive |

These have different lifecycles. Mixing them means an agent can't distinguish "always true" from "was true on 2026-03-28."

**Recommendation — tag each entry with a lifecycle:**

| Lifecycle | Meaning | Example | Archive policy |
|---|---|---|---|
| `permanent` | Always true until explicitly revoked | Human preferences, standing rules | Never archive |
| `decision` | True until superseded | ADR-0005 VCS strategy | Archive when superseded |
| `fact` | True at time of writing, may change | VM IP, test count, version | Archive when verified stale |
| `event` | Happened once | "v0.8.0 shipped" | Archive after session |

### P-3: Security-sensitive content in a plain file

MEMORY.md contains:
- SSH public keys (full keys, lines 115–116)
- VM credentials hint ("Password baked in Terraform via chpasswd")
- IP addresses and VLAN ranges
- Discord webhook URL with token fragment

This file is in the workspace, not encrypted, and read by every agent session.

**Recommendation:**
- Remove SSH public keys — they're in Terraform config and `~/.ssh/`, no need to duplicate in memory
- Remove credential hints — reference the source (`infra-terraform-proxmox/variables.tf`)
- Keep IP ranges (useful for context, not secret)
- Remove webhook URL — reference `docs/stack.md` instead

### P-4: Duplication with SOUL.md and USER.md

| Content | In MEMORY.md | Also in |
|---|---|---|
| "Address as My Lord" | Human section | USER.md line 4 |
| "Does not tolerate fluff" | Human section | USER.md "What Frustrates Him" |
| "Conventional Commits, commitizen" | Standing Rules / Decisions | SOUL.md lines 52–90 |
| "Definition of Done" | Implied in Quality debt section | SOUL.md lines 92–104 |
| "Diagram sync after finalized tasks" | Standing Rules | SOUL.md lines 117–133 |

**Recommendation:** MEMORY.md Human section should be 2 lines:
```markdown
## Human
See USER.md. Key: @yboujraf, "My Lord", UTC, pragmatic, no fluff.
```

Standards and processes live in SOUL.md / AGENTS.md / CONTRIBUTING.md — MEMORY.md references, not duplicates.

### P-5: Chronological organization is wrong for memory

Decisions are grouped by date (2026-03-26, 2026-03-27, 2026-03-28, 2026-03-29). This means:
- To find the VCS strategy, scan 2026-03-27
- To find the VM baseline, scan 2026-03-28
- To find the lib-synology-dsm state, scan 2026-03-29

**An agent looking for "what's the current Terraform setup?" must read the entire file.**

**Recommendation — organize by topic, not date:**

```markdown
## Standing Rules (permanent)
## Infrastructure Decisions
## Library Decisions
## Identity & Auth Decisions
## Operational Notes (archive candidates)
```

Each entry keeps its date as metadata, but grouping is by domain.

---

## What's missing

### M-1: Archive mechanism

No `MEMORY-archive.md` exists. No policy for when entries move from hot to cold. No cap on file size.

### M-2: Staleness indicators

No entry has a "verified" or "last confirmed" date. The agent has no way to know if "vm-netbox-poc-01 (ID 100)" still exists or was destroyed.

**Add to each volatile entry:** `(verified: 2026-03-29)` or `(unverified)`

### M-3: Relationship to Claude Code memory system

This workspace has its own MEMORY.md, but Claude Code also has a memory system at `~/.claude/projects/`. These are two separate memory layers with no integration.

**Clarification needed:** Is MEMORY.md the canonical memory (agent reads it), or is Claude Code's memory system canonical? Currently both exist independently.

**Recommendation:** MEMORY.md is canonical for Rune (workspace agent). Claude Code memory is per-user, per-project. They serve different scopes — document the boundary.

---

## Proposed MEMORY.md structure (after cleanup)

```markdown
# MEMORY.md — Long-Term Memory
> Scope: workspace-level. Cap: 80 lines. Archive: MEMORY-archive.md

## Human
See USER.md. Key: @yboujraf ("My Lord"), UTC, pragmatic, no fluff.

## Standing Rules (permanent)
[current standing rules — 10-15 lines]

## Current Truths (verify before acting)
[infrastructure state, key IPs, active versions — 15-20 lines]
[each entry tagged: (verified: YYYY-MM-DD)]

## Active Decisions (topic-grouped)
[VCS, identity, lib-synology-dsm, terraform — 20-30 lines]
[move to MEMORY-archive.md when implemented + verified]
```

**Total: ~60-80 lines.** Everything else → `MEMORY-archive.md`.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Create `MEMORY-archive.md` — move all date-specific session notes and implemented decisions | HIGH | Medium |
| A2 | Reorganize MEMORY.md by topic (not date) | HIGH | Medium |
| A3 | Set hard cap (~80 lines) + archive policy | HIGH | Low |
| A4 | Remove security-sensitive content (SSH keys, credential hints, webhook tokens) | HIGH | Low |
| A5 | Deduplicate: reduce Human section to 2-line reference to USER.md | MEDIUM | Low |
| A6 | Deduplicate: remove standards that live in SOUL.md/AGENTS.md | MEDIUM | Low |
| A7 | Add staleness indicators `(verified: date)` to volatile facts | MEDIUM | Low |
| A8 | Document relationship: MEMORY.md vs Claude Code memory system | LOW | Low |

---

## Design principles applied

- **Bounded context:** MEMORY.md has a size cap. Unbounded growth is a design flaw, not a feature.
- **Separation of concerns:** Identity → USER.md. Standards → SOUL.md. Memory → MEMORY.md. No duplication across boundaries.
- **CQRS-inspired:** Hot memory (read every session) vs cold archive (read on demand). Different access patterns, different storage.
- **Lifecycle management:** Every entry has a lifecycle (permanent / decision / fact / event) and an archive trigger.
- **Least privilege:** Security-sensitive data referenced by pointer, not stored in a file every agent reads.

---

*To apply: read this audit, confirm actions, then run agent with instructions to execute A1–A8.*
