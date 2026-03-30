# ADR-0007: Consistent Return Dict Contract for All Mutating Methods

**Status:** Accepted
**Date:** 2026-03-30
**Deciders:** @yboujraf

## Context

ADR-0002 defines `ensure()` return semantics as `{"changed": bool, "action": str}`. However, other mutating methods (`create()`, `delete()`, `upload()`) were not covered by the same contract. This led to `FileStation.upload()` returning `{"skipped": bool}` — inconsistent with the rest of the library.

## Decision

**All public methods that mutate state must return `{"changed": bool, "action": str}`.**

This includes:
- `ensure()` and its variants (`ensure_rule()`, `ensure_user()`, `ensure_group()`)
- `create()` / `add()` methods
- `delete()` / `remove()` methods
- `upload()` / `download()` methods

**Standard action strings:**

| Scenario | `changed` | `action` |
|---|---|---|
| Created | True | "created" |
| Updated | True | "updated" |
| Deleted | True | "deleted" |
| Uploaded | True | "uploaded" |
| Already exists (noop) | False | "exists" |
| Dry run | False | "dry_run" |

**`FileStation.upload()` must be updated** to return `{"changed": bool, "action": str}` instead of `{"skipped": bool}`. This is a v1.0 blocker.

## Consequences

**Positive:**
- Consistent interface across all managers — callers can always check `result["changed"]`
- Enables idiomatic usage: `if result["changed"]: log(result["action"])`
- Eliminates ad-hoc return shapes per method

**Negative:**
- `FileStation.upload()` is a breaking change (return dict shape changes)
- Any code checking `result["skipped"]` must be updated

## Supersedes

Extends ADR-0002 to cover all mutating methods, not just `ensure()`.
