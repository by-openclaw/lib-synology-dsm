# Architecture Decision Records

Repo-level architectural decisions for `lib-synology-dsm`.

Platform-wide decisions: [`doc-platform-core/docs/adr/`](https://github.com/by-openclaw/doc-platform-core/tree/main/docs/adr)

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

## Records

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](0001-urllib-over-httpx.md) | Use stdlib urllib instead of httpx | Accepted |
| [ADR-0002](0002-ensure-pattern.md) | Idempotent ensure() pattern for all resource managers | Accepted |
| [ADR-0003](0003-credential-provider-hierarchy.md) | Layered credential provider hierarchy | Accepted |
