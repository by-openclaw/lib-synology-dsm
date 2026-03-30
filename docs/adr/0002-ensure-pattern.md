# ADR-0002: Idempotent ensure() pattern for all resource managers

**Date:** 2026-03-29
**Status:** Accepted

## Context

The library manages DSM resources (shares, users, groups) from automation pipelines (Ansible, Terraform, scripts). Those pipelines run repeatedly and must be idempotent — running the same operation twice must not error or duplicate resources.

## Decision

Every resource manager must implement:

```python
def ensure(
    self,
    name: str,
    state: Literal["present", "absent"] = "present",
    dry_run: bool = False,
    **desired_fields,
) -> dict:
```

Behaviour contract:
1. **Fetch current state** — list existing resources, build a lookup map
2. **Diff** — compare desired fields against current state
3. **Act only if diff** — if state matches, return `{changed: False, action: "noop"}`
4. **dry_run=True** — return what would happen, make zero API calls
5. **Return dict** — always includes `changed` (bool), `action` (str), optionally `before`/`after`

Action strings: `"created"`, `"updated"`, `"deleted"`, `"noop"`, `"would_create"`, `"would_update"`, `"would_delete"`

Destructive methods (`delete()`, `create()`) also accept `dry_run=True`.

## Consequences

**Positive:**
- Safe to call from Ansible modules, Terraform null resources, CI pipelines
- Test-friendly — dry_run=True verifies intent without side effects
- Predictable return shape for callers to log/audit changes

**Negative:**
- Requires an extra `list()` call before every mutation (2 API calls instead of 1)
- More complex implementation than a simple `create()`/`delete()`

## Note

All public methods that mutate state must return `{"changed": bool, "action": str}`. This includes `ensure()` variants, `create()`, `delete()`, and `upload()` methods.
