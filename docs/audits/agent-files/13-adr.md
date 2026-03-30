# Audit: Architecture Decision Records (ADR)

> **Scope:** `lib-synology-dsm/docs/adr/` — all ADRs + index + format + missing decisions
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — missing ADRs for confirmed decisions, minor accuracy issues

---

## Purpose of ADRs

ADRs are the **immutable decision record**. They answer:

1. **What was decided?** (the decision)
2. **Why?** (the context that drove it)
3. **What are the trade-offs?** (consequences — positive and negative)

In this repo, ADRs are the authority behind CLAUDE.md Hard Rules. Every "non-negotiable" should trace to an ADR. If there's no ADR, it's an opinion, not a decision.

---

## Current state

- **Location:** `docs/adr/`
- **Count:** 3 ADRs + 1 index (README.md)
- **Format:** MADR-lite (Context / Decision / Consequences)
- **All dated:** 2026-03-29
- **All status:** Accepted

| ADR | Title | Enforced in |
|---|---|---|
| 0001 | Use stdlib urllib instead of httpx | CLAUDE.md Hard Rules, AGENTS.md What NOT To Do |
| 0002 | Idempotent ensure() pattern for all resource managers | CLAUDE.md Hard Rules |
| 0003 | Layered credential provider hierarchy | CLAUDE.md Hard Rules |

---

## What's good

| Aspect | Verdict | Notes |
|---|---|---|
| Format consistency | Strong | All 3 follow the same Context → Decision → Consequences structure |
| Context sections | Strong | Each explains the *why* clearly — not just what, but the operational constraint driving it |
| Consequences sections | Good | Both positive and negative listed — honest trade-off documentation |
| Index in README.md | Good | Table with links, format template, platform ADR cross-reference |
| Code examples in decisions | Good | ADR-0002 and 0003 include concrete Python signatures and priority logic |

---

## Accuracy issues in existing ADRs

### ADR-0001: urllib — minor inaccuracy

**Line:** "pip install lib-synology-dsm pulls only pydantic"

**Problem:** The library has **zero** runtime deps. `pydantic` is not a dependency — `DSMCredentials` is a plain dataclass, not a Pydantic model. This statement is wrong.

**Fix:** Change to: "pip install lib-synology-dsm pulls zero external packages"

### ADR-0002: ensure() — scope has expanded

**Line:** "Every resource manager (ShareManager, UserManager, GroupManager) must implement"

**Problem:** Only 3 managers listed. There are now 7+ managers with ensure(): Share, User, Group, NFS, FileStation, Quota, Bandwidth (ensure_user/ensure_group), Storage (read-assert), TrafficControl (ensure_rule).

**Fix:** Change to: "Every resource manager must implement" (drop the parenthetical list, or update it to reflect all managers). Consider adding a "Status" or "Adoption" section showing which managers have implemented it.

### ADR-0002: return dict contract not fully specified

The ADR defines `{changed, action}` and lists action strings. But it doesn't specify:
- That `ensure()` variants like `ensure_user()`, `ensure_group()`, `ensure_rule()` follow the same contract
- That non-ensure methods (`upload()`, `download()`) should also return `{changed, action}` (currently `upload()` violates this — returns `{skipped}`)

**Fix:** Add a note: "All public methods that mutate state must return `{changed: bool, action: str}`. This includes `ensure()` and its variants, as well as standalone `create()`, `delete()`, and `upload()` methods."

### ADR-0003: Vault status

**Line:** "Vault AppRole authentication not yet implemented — currently only token auth"

**Problem:** Still accurate, but should note Phase 2 timing: "Vault AppRole planned for Phase 2 — blocked until Vault deployed on PoC."

---

## Missing ADRs — confirmed decisions without records

These decisions were confirmed in the refactor clarification doc or CLAUDE.md but have no ADR:

### ADR-0004: Per-repo documentation and RAID (missing)

**Decision:** Each repo owns its own docs, RAID, and tracking. No centralized docs in `doc-platform-core` for repo-scoped content.

**Context:** Separation of concerns — not everyone has access to every repo. Centralizing creates access gaps and mixes concerns.

**Confirmed:** 2026-03-30, refactor-clarification §6 (Q3, RAID decision)

**Impact:** Changes where RAID.md lives, where api-reference.md lives, doc maintenance workflows.

### ADR-0005: Separate repos per language (missing)

**Decision:** Each library is language-specific. Python for Ansible/file processing. Go/C++ for real-time workloads. No same lib in multiple languages.

**Context:** Different performance profiles require different languages. A Go DSM client would serve different use cases than the Python one.

**Confirmed:** 2026-03-30, refactor-clarification §6 (Q1)

**Impact:** Repo naming (lib-synology-dsm = Python, lib-synology-dsm-go = Go), no multi-language folders in this repo.

### ADR-0006: Timeout and streaming strategy (missing — pending implementation)

**Decision:** Not yet decided in detail, but confirmed as v1.0 blocker. Per-operation timeouts, streaming upload, retry logic.

**Context:** Hardcoded `timeout=30` in `client.py:69` causes upload timeouts on large files. No retry on transient 503s.

**Status:** Should be written when the implementation is designed — before code, not after.

### ADR-0007: Return dict contract (candidate)

**Decision:** All public methods that mutate state return `{"changed": bool, "action": str}`. No exceptions.

**Context:** ADR-0002 implies this but doesn't fully specify it. `FileStation.upload()` currently violates it by returning `{"skipped": bool}`.

**Status:** Could be an amendment to ADR-0002 or a standalone ADR. Recommend standalone — the scope is broader than ensure() (covers upload, delete, etc.).

### ADR-0008: Archive, never delete (candidate)

**Decision:** Historical documentation files are archived to `docs/archive/`, never deleted.

**Context:** Audit trail preservation. Files move at release time.

**Confirmed:** 2026-03-30, refactor-clarification §6 (Q4)

**Status:** Minor — could be a project convention in CONTRIBUTING.md rather than a full ADR. But given the "non-negotiable" tone of the decision, an ADR anchors it.

---

## ADR index (README.md) issues

| Item | Problem | Fix |
|---|---|---|
| Only 3 records listed | Missing ADR-0004 through 0008 | Update index as new ADRs are created |
| Platform ADR cross-reference | Links to `doc-platform-core/docs/adr/` | Verify link still works |
| No status lifecycle | Format shows "Proposed / Accepted / Deprecated / Superseded" but no ADR has ever been deprecated or superseded | Fine for now — will matter when decisions change |

---

## ADR process gaps

### G-1: No ADR template file

The format is documented in README.md but there's no `_template.md` or `0000-template.md` file to copy from.

**Fix:** Add `docs/adr/0000-template.md` — a blank ADR with all sections pre-filled with prompts.

### G-2: No link from CLAUDE.md Hard Rules to ADRs

CLAUDE.md says "Rationale: ADR-0001" but the link is to the filename, not a full path. An agent in a different context might not find it.

**Fix:** Use relative links: `[ADR-0001](docs/adr/0001-urllib-over-httpx.md)`

### G-3: No convention for when to write an ADR

When does a decision warrant an ADR vs just a note in CONTRIBUTING.md?

**Proposed rule:**
- **ADR required:** Decision constrains implementation choices for future contributors (e.g., "never use httpx", "always return {changed, action}")
- **ADR not required:** Operational process (e.g., "run nox for multi-python testing", "commit with conventional format")

**Test:** If violating the decision would break the architecture or require a migration to fix — it's an ADR. If violating it would just be inconsistent — it's a convention.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Fix ADR-0001: remove pydantic reference (zero deps, not "pulls pydantic") | HIGH | Low |
| A2 | Fix ADR-0002: update manager list or remove parenthetical. Add note about return dict scope. | HIGH | Low |
| A3 | Create ADR-0004: per-repo documentation and RAID | HIGH | Low |
| A4 | Create ADR-0005: separate repos per language | MEDIUM | Low |
| A5 | Create ADR-0007: return dict contract (all mutating methods) | MEDIUM | Low |
| A6 | Create ADR-0006: timeout and streaming strategy (write before implementing) | MEDIUM | Medium |
| A7 | Add ADR-0003 Phase 2 note for Vault AppRole | LOW | Low |
| A8 | Add `0000-template.md` to docs/adr/ | LOW | Low |
| A9 | Update README.md index as ADRs are created | LOW | Low |
| A10 | Document "when to write an ADR" convention | LOW | Low |

---

## Design principles applied

- **Decision traceability:** Every CLAUDE.md hard rule traces to an ADR. If it doesn't, the rule is unanchored.
- **Immutability:** ADRs are never edited to change the decision — they are superseded by a new ADR. Accuracy fixes (typos, stale lists) are OK.
- **Separation of concerns:** ADRs = architectural constraints. CONTRIBUTING.md = operational conventions. Different scope, different files.
- **Write before code:** ADR-0006 (timeout strategy) should be written before the implementation starts, not after. The ADR is the design doc.

---

*To apply: A1 and A2 are quick fixes to existing files. A3–A5 are new files — use the template from README.md. A6 depends on timeout design work.*
