# Audit: Workspace-Level Files (.openclaw/workspace/)

> **Scope:** `/home/by-systems/.openclaw/workspace/` — all non-repo files
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — file sprawl, stale memory logs, secrets in infra/

---

## Inventory

### Core identity files (active, read every session)

| File | Lines | Status | Audited in |
|---|---|---|---|
| SOUL.md | 85 | Active — scope creep (operational content) | [03-soul-md.md](03-soul-md.md) |
| USER.md | 66 | Active — cleanest file | [05-user-md.md](05-user-md.md) |
| MEMORY.md | 67 | Active — recently restructured, ~80 line cap | [04-memory-md.md](04-memory-md.md) |
| MEMORY-archive.md | ~200 | Active — receives archived content from MEMORY.md | New |
| AGENTS.md | 271 | Active — workspace-level agent onboarding | New |
| IDENTITY.md | 9 | Active — simple identity card | New |
| HEARTBEAT.md | 20 | Active — periodic check directives | New |
| TOOLS.md | ~80 | Partial — SSH keys section empty | New |

### Directories

| Directory | Contents | Status |
|---|---|---|
| `memory/` | 7 daily session logs (2026-03-21 to 2026-03-28) + 2 JSON state files | **Stale** — daily logs should be archived |
| `docs/` | architecture.md, naming-convention.md, roadmap.md, raid.md, stack.md + adr/ + templates/ | **Duplicates doc-platform-core** |
| `infra/` | 6 audit reports + network inventory + secrets/ | **Contains secrets** |
| `diagrams/` | 5 diagram files (PNG + PlantUML + Python + ASCII) | Current (2026-03-28) |
| `assets/` | Template asset library (diagrams, docs, exports, images, media) | Template structure |
| `repos/` | 5 git repos | Active |

---

## Critical issues

### C-1: `docs/` duplicates doc-platform-core

The workspace has its own `docs/` directory with:
- architecture.md, naming-convention.md, roadmap.md, raid.md, stack.md
- docs/adr/ (at least 0001)
- docs/templates/

**These are the same files that exist in `repos/doc-platform-core/docs/`.** Which is canonical?

**Recommendation:** `repos/doc-platform-core/` is the git-tracked canonical source. `workspace/docs/` should either:
- Be a symlink to `repos/doc-platform-core/docs/`
- Or be removed entirely (use repo directly)

Having two copies guarantees drift.

### C-2: `docs/stack.md` contains exposed Discord webhook token

Already flagged in [audit 16](16-secrets-redaction.md) — the workspace copy has the full token at lines 437, 447. **CRITICAL — redact and rotate.**

### C-3: `memory/` daily logs are stale

7 session logs from 2026-03-21 to 2026-03-28. These were the source material for MEMORY.md and MEMORY-archive.md. Now that those curated files exist, the raw logs serve no purpose.

**Recommendation:** Archive or delete. They contain passwords and sensitive content (see audit 16, workspace/memory/2026-03-26.md and 2026-03-27.md).

### C-4: `infra/` contains sensitive audits

- `.proxmox-nonprod.env` — environment config (restricted perms)
- `secrets/` — not explored but name implies sensitive content
- Audit reports contain IP ranges, device names, credentials context

**Recommendation:** This directory is useful but should not be committed to any repo. Verify it's gitignored at workspace level.

### C-5: Workspace AGENTS.md vs repo AGENTS.md — role confusion

The workspace has its own `AGENTS.md` (271 lines) alongside repo-level AGENTS.md files. The workspace version covers session startup, sync rules, project health philosophy. Repo-level versions cover repo-specific onboarding.

**This is actually correct** — workspace AGENTS.md is the "how to be Rune" file, repo AGENTS.md is "how to work in this repo." But the relationship isn't documented anywhere.

**Add to SOUL.md file hierarchy:**
```
workspace/AGENTS.md  → how to be Rune (session startup, sync rules)
{repo}/AGENTS.md     → how to work in this specific repo
```

### C-6: IDENTITY.md vs SOUL.md overlap

IDENTITY.md (9 lines) is a subset of SOUL.md §Identity. Both define name, role, vibe.

**Recommendation:** Remove IDENTITY.md. SOUL.md covers everything it says and more. Or repurpose IDENTITY.md as a machine-readable identity card (JSON/YAML) if tooling needs it.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Resolve workspace/docs/ duplication with doc-platform-core (symlink or remove) | HIGH | Low |
| A2 | Redact Discord webhook token in workspace/docs/stack.md | CRITICAL | Low |
| A3 | Archive or delete memory/ daily logs (contain passwords) | HIGH | Low |
| A4 | Verify infra/ and secrets/ are not git-tracked | MEDIUM | Low |
| A5 | Document workspace AGENTS.md vs repo AGENTS.md relationship | MEDIUM | Low |
| A6 | Remove or repurpose IDENTITY.md (subset of SOUL.md) | LOW | Low |
| A7 | Archive TOOLS.md SSH keys section or fill it in | LOW | Low |

---

*The workspace is the agent's home. It should be clean, secure, and unambiguous about what's canonical.*
