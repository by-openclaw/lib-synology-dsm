# Audit: README.md

> **Scope:** `lib-synology-dsm/README.md`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — stale content, missing managers, version/test count drift

---

## Purpose of README.md

README.md is the **public face** of the repo. First thing anyone sees — human or agent. It answers:

1. **What is this?** (one-liner)
2. **How do I install it?** (quick start)
3. **How do I use it?** (code examples)
4. **What's the current state?** (badges, feature list)
5. **Where do I go next?** (docs links)

Standing rule from SOUL.md: "README reflects actual state — not aspirational."

---

## Current state

- **Version shown:** 0.9.3 (via badge)
- **Test count:** 283 unit tests, 51 integration tests
- **Managers listed:** DSMClient, ShareManager, UserManager, GroupManager, FileStationManager, NFSManager, QuotaManager, BandwidthManager, StorageManager, TrafficControlManager
- **Badges:** CI, version, coverage, Python versions, pre-commit, dev container, license

---

## What's good

| Section | Verdict | Notes |
|---|---|---|
| Badges | Good | Comprehensive, linked, auto-updating where possible |
| Quick start code example | Strong | Shows DSMClient + ensure() pattern — the core value prop |
| Documentation table | Good | Links to 8 docs — clear entry points |
| Error handling section | Good | try/except examples with typed exceptions |
| Internal use notice | Good | Sets expectations |
| Manager list | Current | All 10 managers listed including TrafficControlManager |

---

## What's stale or at risk

| Item | Problem | Fix |
|---|---|---|
| Test count | Says 283 — will drift with every new test | Consider: "280+ unit tests" or auto-generate from CI badge |
| Version badge | Auto-updates via shield — OK | No action |
| Python 3.13 badge | Listed — verify CI actually tests 3.13 | Cross-check with CI workflow |
| "100% coverage" claim | Verify — is it actually 100% on current main? | If yes, keep. If drifted, update. |

---

## What's missing

### M-1: No v1.0 roadmap mention

README says the project is v0.9.3 but doesn't indicate what's coming or what's blocking v1.0. A one-liner would set expectations:

```markdown
> **Next milestone:** v1.0.0 — see [priority matrix](docs/refactor-clarification-2026-03-30.md) for blockers.
```

### M-2: No mention of ensure() dry_run in quick start

The quick start shows `ensure()` but not `dry_run=True`. This is a key differentiator — safe preview before mutation. One example line would demonstrate it.

### M-3: No TrafficControlManager or BandwidthManager usage examples

Only ShareManager is shown in quick start. The newer managers (quota, bandwidth, traffic control) have no code examples in README. Not every manager needs one, but bandwidth/traffic control ensure patterns are non-obvious.

**Recommendation:** Add a "More Examples" section or link to `docs/api-reference.md` for each manager.

### M-4: SECURITY.md supported version is stale

SECURITY.md says "0.8.x current" but the project is at 0.9.3. This isn't a README issue, but README links to SECURITY.md — any reader clicking through sees stale info.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Add v1.0 roadmap one-liner with link to refactor doc | MEDIUM | Low |
| A2 | Add dry_run=True example to quick start | LOW | Low |
| A3 | Add "More Examples" section or manager usage links | LOW | Medium |
| A4 | Verify test count and coverage claim match CI | MEDIUM | Low |
| A5 | Update SECURITY.md supported version (0.8.x → 0.9.x) | MEDIUM | Low |

---

## Design principles applied

- **Accuracy over aspiration:** README shows what exists, not what's planned. Roadmap is one line with a link.
- **Progressive disclosure:** Quick start is enough to get started. Detailed API → docs/api-reference.md.
- **Single source of truth:** Version comes from pyproject.toml via badge. Test count should come from CI, not a hardcoded number.

---

*To apply: confirm actions, then update README.md and SECURITY.md together.*
