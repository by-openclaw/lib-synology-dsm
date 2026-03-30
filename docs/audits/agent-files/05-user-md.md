# Audit: USER.md

> **Scope:** `/home/by-systems/.openclaw/workspace/USER.md` (workspace-level)
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** MINOR — cleanest file of the set, small improvements only

---

## Purpose of USER.md

USER.md defines **who the human is** — the agent's understanding of the person it serves. It answers:

1. **Who is this person?** (name, role, org)
2. **What do they care about?** (values, priorities)
3. **What frustrates them?** (anti-patterns to avoid)
4. **What are they building?** (project context)
5. **How should I communicate?** (tone, style)

USER.md is the counterpart to SOUL.md. SOUL = agent identity. USER = human identity. Together they define the working relationship.

---

## Current state

- **Location:** `/home/by-systems/.openclaw/workspace/USER.md`
- **Lines:** 57
- **Last updated:** 2026-03-29
- **Sections:** 8 (Who He Is, What He Cares About, What Frustrates Him, What He's Building, His Reference Standard, Context in Discord, Notes)

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Who He Is | Strong | Concise, respectful, accurate. |
| What He Cares About | Strong | 5 clear priorities, actionable for any agent. |
| What Frustrates Him | Strong | Specific anti-patterns, not vague. Directly guides agent behavior. |
| What He's Building | Good | Full stack inventory. Useful for context. |
| His Reference Standard | Excellent | The brother benchmark is motivating and concrete. |
| Notes | Good | Communication style preferences. |

**This is the best-written file of the five.** It's focused, respectful, and actionable.

---

## What's problematic

### P-1: Minor — "What He's Building" will go stale

The tech stack list (lines 34–40) is a snapshot. When components are added/removed/replaced, this list drifts.

**Recommendation:** Keep it, but add a reference:
```markdown
For current stack state: see `doc-platform-core/docs/stack.md` (if it exists) or `doc-platform-core/docs/adr/0006-platform-charter.md`
```

The list in USER.md stays as "intent" — what he's building toward. The authoritative current state lives in the platform docs.

### P-2: Minor — Discord context section is agent-platform-specific

Lines 48–49 reference `memory_search` / `memory_get` — these are OpenClaw/Discord-specific commands, not relevant to all agent contexts (e.g., Claude Code CLI, VS Code extension, Codex).

**Recommendation:** Move Discord-specific operational context to MEMORY.md or a dedicated `DISCORD.md`. USER.md should describe the human, not the communication platform's API.

### P-3: Duplication with MEMORY.md

| Content | USER.md | MEMORY.md |
|---|---|---|
| "Address as My Lord" | Line 4 | Human section |
| "Prefers pragmatic, structured" | Notes section | Human section |
| "Does not tolerate fluff" | What Frustrates Him | Human section |
| Timezone: UTC | Line 7 | Human section |

**Recommendation:** MEMORY.md Human section becomes a 2-line pointer to USER.md. USER.md is the single source of truth for human context.

---

## What's missing

### M-1: No scope declaration

USER.md doesn't state its scope. Add:
```markdown
> **Scope:** Workspace-level — describes the human owner across all repos and sessions
```

### M-2: No relationship to other files

Unlike SOUL.md (which has Continuity section) and MEMORY.md (which references other files), USER.md is standalone. Add a small context line:

```markdown
> **Related:** SOUL.md (agent identity), MEMORY.md (session memory)
```

### M-3: No "How to disagree" guidance

SOUL.md says "Have opinions and hold them" and "I'm allowed to push back." USER.md says "Appreciates when I push back if something is wrong."

But neither file describes **how** to disagree effectively with this specific human. What format works? What tone? Based on the user profile:

**Add to Notes:**
```markdown
- When pushing back: lead with the fact or risk, then the recommendation. No preamble, no softening. "This will break X because Y. Recommend Z instead." He respects direct disagreement, not diplomatic hedging.
```

### M-4: No update trigger

When should USER.md be updated? Currently unclear.

**Add:**
```markdown
## Update Policy
- Updated when learning new preferences, frustrations, or context about My Lord
- Never updated with ephemeral session details (those go in MEMORY.md)
- Changes communicated in session
```

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Add scope declaration + relationship to other files | MEDIUM | Low |
| A2 | Add stack reference pointer (platform charter/stack.md) | LOW | Low |
| A3 | Move Discord-specific context to MEMORY.md or DISCORD.md | LOW | Low |
| A4 | Ensure MEMORY.md Human section points to USER.md (no duplication) | MEDIUM | Low |
| A5 | Add "How to disagree" guidance in Notes | LOW | Low |
| A6 | Add update policy | LOW | Low |

---

## Design principles applied

- **Single source of truth:** USER.md is the canonical human profile. MEMORY.md references it.
- **Separation of concerns:** USER.md = who the human is. MEMORY.md = what happened. No overlap.
- **Interface segregation:** An agent that only reads USER.md knows how to communicate. It doesn't need MEMORY.md for that.
- **Stable vs volatile:** USER.md is stable (personality doesn't change per session). MEMORY.md is volatile (events change every session). Different files for different change rates.

---

*To apply: read this audit, confirm actions, then run agent with instructions to execute A1–A6.*
