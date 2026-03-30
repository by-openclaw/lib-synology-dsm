# ADR-0004: Per-Repo Documentation and RAID

**Status:** Accepted
**Date:** 2026-03-30
**Deciders:** @yboujraf

## Context

The platform uses a centralized `doc-platform-core/docs/raid.md` for RAID tracking (ADR-0003). As the number of repos grows, repo-scoped risks and decisions (e.g., timeout gap in lib-synology-dsm, upload return dict violation) were being added to the platform RAID, mixing concerns and creating access gaps.

A decision was needed: per-repo, centralized, or hybrid.

## Decision

**Hybrid model:**

- **Per-repo `RAID.md`:** Tracks risks, issues, and dependencies scoped to a single repo (e.g., mypy errors, v1.0 blockers, API quirks).
- **`doc-platform-core/docs/raid.md`:** Tracks cross-repo risks, infrastructure dependencies, and compliance items (e.g., TLS strategy, Vault integration, platform-wide blockers).

**Rule:** If the risk affects one repo only → repo's `RAID.md`. If it crosses repos or affects the platform → `doc-platform-core/docs/raid.md`.

Per-repo documentation follows the same model: `docs/adr/`, `docs/api-reference.md`, and similar files are owned by each repo.

## Consequences

**Positive:**
- Separation of concerns: repo maintainers own their risk register
- Access-scoped: no cross-repo visibility issues
- Compliance view preserved: platform RAID still exists for auditors

**Negative:**
- Two RAID files to maintain
- Agents must know which RAID to update (rule: scope determines location)

## Supersedes

Partially supersedes ADR-0003 §RAID location. ADR-0003 is amended to reflect the hybrid model.
