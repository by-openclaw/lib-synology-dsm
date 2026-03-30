# Audit: CONTRIBUTING.md

> **Scope:** `lib-synology-dsm/CONTRIBUTING.md`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — missing sections, will receive content from SOUL.md/AGENTS.md cleanup

---

## Purpose of CONTRIBUTING.md

CONTRIBUTING.md is the **developer onboarding and workflow guide**. It answers:

1. **How do I set up the project?** (environment, deps, credentials)
2. **How do I run tests?** (unit, integration, smoke)
3. **How do I submit changes?** (commit format, PR process, release)
4. **What quality gates must I pass?** (linting, type checking, coverage)

This file is the natural destination for operational processes being moved out of SOUL.md, AGENTS.md, and CLAUDE.md.

---

## Current state

- **Lines:** ~120 (estimated from summary)
- **Last updated:** ~v0.7.2 era
- **Sections:** Setup (Path A: native, Path B: dev container), Credentials, Pre-commit hooks, LAN access, Release process

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Two setup paths (native + container) | Strong | Inclusive, well-documented, OS-aware |
| Credentials setup | Good | .env.example pattern, clear instructions |
| Pre-commit hooks | Good | Specific tools listed |
| Release process | Good | "Never manually edit" is clear |

---

## What's stale

| Item | Problem | Fix |
|---|---|---|
| No mention of nox | nox is used for multi-python CI parity locally. Not documented. | Add nox section |
| Supported versions | SECURITY.md says 0.8.x, pyproject says 0.9.3, README says 0.9.3 | Align — CONTRIBUTING should reference pyproject as source of truth |
| LAN access from container | "macOS/Ubuntu pending" | Verify and update — was this tested? |
| No mention of TrafficControlManager, QuotaManager, BandwidthManager, StorageManager | Feature coverage has grown since CONTRIBUTING was written | Not needed in CONTRIBUTING (it's about process, not features) — but integration test examples should reference current managers |

---

## What's missing — content to receive from other files

### M-1: Commit & Version Standard (from SOUL.md)

SOUL.md lines 52–90 contain the full conventional commit standard, version bump table, and workflow. This belongs here.

**Proposed section:**
```markdown
## Commit Standard
[Move SOUL.md lines 52–90 here — conventional commits format, version bump table, workflow]
```

### M-2: Definition of Done checklist (from SOUL.md)

SOUL.md lines 92–104 contain the DoD checklist. The checklist version (not the principles) belongs in CONTRIBUTING.md as a PR submission checklist.

**Proposed section:**
```markdown
## Definition of Done — PR Checklist
- [ ] All public methods have docstrings
- [ ] ensure() / idempotent pattern where applicable
- [ ] dry_run=True mode where applicable
- [ ] Unit tests — happy path + error codes
- [ ] Integration test — live or mocked
- [ ] PEP 8 + PEP 257 clean (ruff)
- [ ] Type hints on all public API (mypy clean)
- [ ] CHANGELOG entry
- [ ] Git tag (via Release Please)
- [ ] CLAUDE.md + AGENTS.md updated if state changed
```

### M-3: Diagram Standard (from SOUL.md)

SOUL.md lines 117–133 describe the diagram pipeline. This is a contribution process.

**Proposed section:**
```markdown
## Diagram Standard
- Source: PlantUML `.puml` → `assets/diagrams/`
- Render: PNG via Kroki → `assets/exports/`
- ASCII version → `assets/diagrams/`
- Commit all three
- Docs link to `assets/exports/` only
```

### M-4: Post-Release Checklist (from AGENTS.md)

AGENTS.md "Doc Maintenance" section describes the post-build update ritual. This is a release process step.

**Proposed section:**
```markdown
## Post-Release Checklist
After each release (CI green, tag created):
- [ ] AGENTS.md — update Project Stats
- [ ] CLAUDE.md — update Current State if changed
- [ ] README.md — update badges, feature lists, version
- [ ] Commit: `docs: update project docs to v{version}`
```

### M-5: How to run nox

Missing entirely. Nox is used for multi-python testing locally.

**Proposed section:**
```markdown
## Multi-Python Testing (nox)
```bash
nox          # run all sessions (lint + test on 3.10/3.11/3.12/3.13)
nox -s test  # test only
nox -s lint  # lint only
```
```

### M-6: Branch naming convention

AGENTS.md mentions `feat/{issue-id}-{description}` but CONTRIBUTING.md doesn't.

**Add to Commit Standard section:**
```markdown
### Branch naming
- `feat/{issue-id}-{description}` — new features
- `fix/{issue-id}-{description}` — bug fixes
```

### M-7: Integration test prerequisites

The Known Blocker in AGENTS.md (DSM account requirements) is critical for integration testing but not in CONTRIBUTING.md.

**Add section or link:**
```markdown
## Integration Test Prerequisites
See AGENTS.md §Known Blocker for required DSM account configuration.
```

---

## Structural recommendation

Proposed section order for CONTRIBUTING.md after receiving moved content:

```
1. Quick Start (setup)
   1a. Path A: Native
   1b. Path B: Dev Container
2. Credentials
3. Running Tests
   3a. Unit tests
   3b. Integration tests (+ prerequisites link)
   3c. Multi-python (nox)
   3d. Smoke tests (curl)
4. Commit Standard (from SOUL.md)
5. Branch Naming
6. Definition of Done — PR Checklist (from SOUL.md)
7. Diagram Standard (from SOUL.md)
8. Pre-commit Hooks
9. Release Process
10. Post-Release Checklist (from AGENTS.md)
```

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Receive Commit & Version Standard from SOUL.md | HIGH | Low |
| A2 | Receive DoD checklist from SOUL.md | HIGH | Low |
| A3 | Receive Diagram Standard from SOUL.md | MEDIUM | Low |
| A4 | Receive Post-Release Checklist from AGENTS.md | MEDIUM | Low |
| A5 | Add nox section | MEDIUM | Low |
| A6 | Add branch naming convention | LOW | Low |
| A7 | Add integration test prerequisites (link to AGENTS.md) | LOW | Low |
| A8 | Verify LAN access from container — update or remove "pending" | LOW | Low |

---

## Design principles applied

- **Single responsibility:** CONTRIBUTING.md owns all "how to contribute" processes. No process lives in identity files.
- **Receiver pattern:** This file is the target for content being factored out of SOUL.md and AGENTS.md. The moves are coordinated — source removes, target receives, in the same PR.
- **Progressive disclosure:** Quick start first, advanced topics (nox, diagrams) later. A new contributor reads top-down and stops when they have enough.

---

*To apply: coordinate with 03-soul-md.md (A1, A2) and 02-agents-md.md (A8) — content moves must happen atomically.*
