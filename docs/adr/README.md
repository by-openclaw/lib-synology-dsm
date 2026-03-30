# Architecture Decision Records

Repo-level architectural decisions for `lib-synology-dsm`.

Platform-wide decisions: [`doc-platform-core/docs/adr/`](https://github.com/by-openclaw/doc-platform-core/tree/main/docs/adr)

> When referencing across scopes, use full link [ADR-0001](docs/adr/0001-...) to disambiguate from platform ADRs.

## Format

```
NNNN-short-title.md
```

```markdown
# ADR-NNNN: Title
**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Context
## Decision
## Consequences
```

## Template

Use [0000-template.md](0000-template.md) as a starting point for new ADRs.

## Records

| ADR | Title | Status | Date |
|---|---|---|---|
| [ADR-0001](0001-urllib-over-httpx.md) | Use stdlib urllib instead of httpx | Accepted | 2026-03-29 |
| [ADR-0002](0002-ensure-pattern.md) | Idempotent ensure() pattern for all resource managers | Accepted | 2026-03-29 |
| [ADR-0003](0003-credential-provider-hierarchy.md) | Layered credential provider hierarchy | Accepted | 2026-03-29 |
| [ADR-0004](0004-per-repo-documentation-and-raid.md) | Per-repo documentation and RAID | Accepted | 2026-03-30 |
| [ADR-0005](0005-separate-repos-per-language.md) | Separate repos per language | Accepted | 2026-03-30 |
| [ADR-0007](0007-return-dict-contract.md) | Consistent return dict contract for all mutating methods | Accepted | 2026-03-30 |

> **Note:** ADR-0006 (timeout strategy) is a pending platform decision. Number reserved.
