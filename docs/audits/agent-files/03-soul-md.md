# Audit: SOUL.md

> **Scope:** `/home/by-systems/.openclaw/workspace/SOUL.md` (workspace-level)
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — scope creep, duplication with repo files, missing boundaries

---

## Purpose of SOUL.md

SOUL.md defines **who the agent is** — identity, values, behavioral contract. It is the agent's constitution.

It answers:
1. **Who am I?** (name, role, personality)
2. **What do I believe?** (core truths, non-negotiables)
3. **How do I operate?** (standards, boundaries, continuity)

SOUL.md is **workspace-level** — it applies to all repos, all sessions. It should not contain repo-specific details, volatile state, or operational checklists.

---

## Current state

- **Location:** `/home/by-systems/.openclaw/workspace/SOUL.md`
- **Lines:** ~137
- **Last updated:** 2026-03-29
- **Sections:** 9 (Identity, Core Truths, What I Build Toward, Professional Context, Commit & Version Standard, Continuity, Boundaries, Diagram Standard)

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Identity | Strong | Clear, concise, personality defined. |
| Core Truths | Strong | Opinionated, specific, actionable. "Nothing ships at 60%" is the north star. |
| What I Build Toward | Good | Vision is clear — async, fire-and-forget, notification-driven. |
| Continuity | Good | "These files are my memory" — essential for session-based agents. |
| Boundaries | Good | Private things, no half-baked output, ask before external actions. |

---

## What's problematic

### P-1: Scope creep — SOUL.md contains operational details (critical)

SOUL.md should be **timeless identity**. Currently it contains:

| Content | Problem | Should live in |
|---|---|---|
| Commit & Version Standard (lines 52–90) | Operational process, not identity | CONTRIBUTING.md or AGENTS.md |
| Definition of Done checklist (lines 92–104) | Repo-level checklist, not agent identity | AGENTS.md (universal) or CLAUDE.md (repo-specific) |
| Diagram Standard (lines 117–133) | Operational process | CONTRIBUTING.md or a dedicated `docs/diagram-standard.md` |
| commitizen config details (`.cz.toml`) | Tool configuration | CONTRIBUTING.md |

**The test:** If Rune moved to a different project with different tools, which parts of SOUL.md would still apply?

- Identity, Core Truths, What I Build Toward, Continuity, Boundaries → **yes** (timeless)
- Commit format, DoD checklist, diagram pipeline → **no** (project-specific)

**Recommendation:** SOUL.md should be ~60 lines, not ~137. Move operational content out.

### P-2: DoD duplication — three copies

The Definition of Done appears in:
1. SOUL.md lines 92–104 (most detailed)
2. CLAUDE.md "Definition of Done" section
3. AGENTS.md (implied in Health Rules)

Three sources that can drift independently.

**Recommendation — single owner pattern:**

| Option | Pros | Cons |
|---|---|---|
| A: DoD lives in SOUL.md only, others reference it | Identity-driven, agent carries it everywhere | Workspace-level file — not visible inside repo without reading up |
| B: DoD lives in CONTRIBUTING.md, others reference it | Standard location for contribution rules | Not agent-native |
| C: DoD lives in AGENTS.md, others reference it | Visible to all agents at repo level | Mixes onboarding with standards |

**Recommended: Option A** — DoD is a core truth, not a process. It belongs in SOUL.md. CLAUDE.md and AGENTS.md say: "Definition of Done: see SOUL.md." One line, no duplication.

### P-3: Commit standard is too detailed for SOUL.md

Lines 52–90 contain a full commit workflow tutorial including bash examples, version bump table, and "Never" list. This is useful but it's a **how-to**, not a **who-I-am**.

**Move to:** AGENTS.md (the universal onboarding file) or CONTRIBUTING.md.

SOUL.md should keep one line:
```markdown
**Commits:** Conventional Commits, enforced. See AGENTS.md or CONTRIBUTING.md for format.
```

### P-4: Diagram standard is operational

Lines 117–133 describe the PlantUML/Kroki/PNG pipeline, marketing image generation, and LFS rules. This is a process standard.

**Move to:** CONTRIBUTING.md or `docs/diagram-standard.md`. SOUL.md should keep one line:
```markdown
**Diagrams:** PlantUML source + Kroki PNG. See CONTRIBUTING.md for pipeline.
```

### P-5: "My Lord" phrasing — consistent but consider audience

SOUL.md uses "My Lord" throughout. This is fine for Rune's personal identity file. But if other agents (Codex, Gemini) read SOUL.md, they need to understand the reference.

**Current:** "My Lord gave me access to his infrastructure"
**Consider adding at top:** `Owner: Yassine Boujraf (@yboujraf) — referred to as "My Lord" throughout.`

One line of context, no phrasing changes needed elsewhere.

---

## What's missing

### M-1: No repo-level vs workspace-level boundary stated

SOUL.md doesn't say where it applies. An agent might assume it's repo-specific.

**Add at top:**
```markdown
> **Scope:** Workspace-level — applies to all repos under `.openclaw/workspace/repos/`
```

### M-2: No versioning or update policy

SOUL.md says "This file is mine to evolve" but doesn't state when updates happen or how changes are communicated.

**Add:**
```markdown
## Update Policy
- Updated when core truths, boundaries, or identity change — not for operational details
- Changes communicated to My Lord in the session they're made
- Operational standards (commit format, diagram pipeline) live in CONTRIBUTING.md, not here
```

### M-3: No relationship map to other files

An agent reading SOUL.md doesn't know how it relates to USER.md, MEMORY.md, CLAUDE.md, AGENTS.md.

**Add:**
```markdown
## File Hierarchy
- **SOUL.md** (this file) — who I am. Workspace-level.
- **USER.md** — who My Lord is. Workspace-level.
- **MEMORY.md** — what I remember. Workspace-level.
- **AGENTS.md** — repo onboarding for any agent. Per-repo.
- **CLAUDE.md** — Claude-specific contract. Per-repo.
```

---

## Proposed SOUL.md structure (after cleanup)

```
1. Identity (name, role, org, vibe)
2. Scope + File Hierarchy (new)
3. Core Truths (keep as-is — this is the heart)
4. What I Build Toward (keep — the vision)
5. Professional Context (keep — trimmed, no tool details)
6. Boundaries (keep)
7. Continuity (keep)
8. Update Policy (new)
```

**Removed / moved out:**
- Commit & Version Standard → AGENTS.md or CONTRIBUTING.md
- Definition of Done checklist → stays in SOUL.md as core truth, but as principles not checklist. Checklist version moves to CONTRIBUTING.md
- Diagram Standard → CONTRIBUTING.md

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Move Commit & Version Standard to AGENTS.md or CONTRIBUTING.md | HIGH | Low |
| A2 | Move Diagram Standard to CONTRIBUTING.md | HIGH | Low |
| A3 | Simplify DoD in SOUL.md to principles; move checklist to CONTRIBUTING.md | MEDIUM | Low |
| A4 | Add scope declaration (workspace-level) | MEDIUM | Low |
| A5 | Add file hierarchy / relationship map | MEDIUM | Low |
| A6 | Add owner context line for "My Lord" reference | LOW | Low |
| A7 | Add update policy section | LOW | Low |
| A8 | Ensure CLAUDE.md and AGENTS.md reference SOUL.md for DoD (no duplication) | HIGH | Low |

---

## Design principles applied

- **Single responsibility:** SOUL.md = identity. Not process, not checklists, not tool configs.
- **Open/closed:** Core truths are closed to modification (stable identity). Operational details are open to change (belong in mutable files).
- **DRY:** DoD has one canonical source. All other files reference, not duplicate.
- **Layered architecture:** Workspace files (SOUL, USER, MEMORY) set context. Repo files (AGENTS, CLAUDE) inherit and specialize.

---

*To apply: read this audit, confirm actions, then run agent with instructions to execute A1–A8.*
