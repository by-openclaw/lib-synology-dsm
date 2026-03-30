# Audit: CHANGELOG.md

> **Scope:** `lib-synology-dsm/CHANGELOG.md`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** MINOR — well-maintained, small consistency issues

---

## Purpose of CHANGELOG.md

CHANGELOG.md is the **release history**. It answers:

1. **What changed in each version?** (features, fixes, breaking changes)
2. **When was it released?** (dates)
3. **Why?** (context, linked commits/issues)

Managed by Release Please — mostly auto-generated from conventional commits.

---

## Current state

- **Versions tracked:** v0.4.1 through v0.9.3 + [Unreleased]
- **Format:** Keep a Changelog + Conventional Commits references
- **Auto-managed:** Yes, via Release Please

---

## What's good

| Aspect | Verdict | Notes |
|---|---|---|
| Consistent format | Strong | Every entry has type, description, commit ref |
| Date on every release | Good | ISO 8601 format |
| [Unreleased] section | Good | Shows in-flight work (bandwidth, traffic control) |
| Commit hash references | Good | Traceability to git history |

---

## Issues

| Item | Problem | Fix |
|---|---|---|
| [Unreleased] section | Lists bandwidth + traffic control as unreleased, but these are committed and tested. Should they be in a release? | Either cut a release (v0.10.0) or keep as-is until v1.0 decision |
| Rapid-fire releases | v0.9.0 through v0.9.3 all on 2026-03-30. Four releases in one day suggests CI iteration, not feature releases. | Not a problem per se — Release Please drives this. But consider squashing fix-only releases pre-v1.0 |
| No link to GitHub Releases | CHANGELOG doesn't link to GitHub Release pages | Add footer: `[v0.9.3]: https://github.com/by-openclaw/lib-synology-dsm/releases/tag/v0.9.3` |

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Decide: cut v0.10.0 for bandwidth + traffic control, or hold for v1.0 | MEDIUM | Decision only |
| A2 | Add GitHub Release links at footer (Release Please may do this automatically) | LOW | Low |

---

## Design principles applied

- **Automation over manual:** Release Please owns this file. Human edits should be rare.
- **Traceability:** Every entry links to a commit. This is correct and should continue.

---

*Lowest priority of all audits. CHANGELOG is healthy.*
